# ipam/allocator.py

import ipaddress
import logging

logger = logging.getLogger(__name__)

class IPAMAllocator:
    def __init__(self, supernet_cidr, used_subnets=None):
        # Supernet is the full available address space (e.g. 10.0.0.0/8)
        self.supernet = ipaddress.ip_network(supernet_cidr, strict=False)
        self.used_subnets = set(ipaddress.ip_network(s, strict=False) for s in (used_subnets or []))
        self.network_blocks = []  # Store assigned /16 blocks to networks for vlan mapping

    def allocate_network_block(self, prefixlen):
        """
        Allocate a large network block from the supernet (e.g. a /16 per network).
        """
        for candidate in self.supernet.subnets(new_prefix=prefixlen):
            if all(not candidate.overlaps(used) for used in self.used_subnets):
                self.used_subnets.add(candidate)
                self.network_blocks.append(candidate)
                logger.debug(f"Allocated network block: {candidate}")
                return str(candidate)
        raise ValueError("No available network blocks left in supernet")

    def allocate_vlan_subnet(self, network_block_cidr, vlan_id, prefixlen):
        """
        Allocate a subnet within a network block, attempting to align address structure
        based on VLAN ID. Works best when block is /16 and prefixlen is /24, but generalizes.

        E.g. 10.10.0.0/16 with vlan_id=20 and prefixlen=24 → 10.10.20.0/24
        """

        logger.debug(f"Allocating VLAN {vlan_id} in network block {network_block_cidr}")

        block = ipaddress.ip_network(network_block_cidr, strict=False)
        host_bits = 32 - prefixlen
        block_size = 1 << host_bits

        base = int(block.network_address)
        offset = vlan_id * block_size
        candidate_net = ipaddress.ip_network((base + offset, prefixlen))

        if candidate_net in self.used_subnets:
            raise ValueError(f"CIDR {candidate_net} already allocated")
        if not candidate_net.subnet_of(block):
            raise ValueError(f"{candidate_net} not within block {block}")

        self.used_subnets.add(candidate_net)
        logger.debug(f"Allocated VLAN subnet {candidate_net} for VLAN ID {vlan_id}")
        return str(candidate_net)

    def mark_used(self, cidr):
        """
        Mark a CIDR as used (e.g., from pre-existing infrastructure).
        """
        self.used_subnets.add(ipaddress.ip_network(cidr, strict=False))

    def allocate_ip(self, subnet_cidr, offset):
        """
        Returns a specific IP within a subnet, based on offset.
        """
        subnet = ipaddress.ip_network(subnet_cidr, strict=False)
        hosts = list(subnet.hosts())
        if offset >= len(hosts):
            raise IndexError("Offset exceeds available host addresses")
        return str(hosts[offset])
    
    def allocate_subnet(self, prefixlen):
        """
        Allocate a generic subnet (e.g., /30, /25, /26) from any previously assigned network block.
        This avoids VLAN alignment logic and simply finds the next available subnet.
        """
        for block in self.network_blocks:
            for candidate in ipaddress.ip_network(block).subnets(new_prefix=prefixlen):
                if all(not candidate.overlaps(used) for used in self.used_subnets):
                    self.used_subnets.add(candidate)
                    logger.debug(f"Allocated generic subnet: {candidate}")
                    return str(candidate)
        raise ValueError("No available subnets left in network blocks")

