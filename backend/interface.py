# backend/interface.py

from abc import ABC, abstractmethod

class BackendProvider(ABC):
    """
    Abstract base class for backend providers.
    Implementations may fetch data from local YAML, NetBox, InfraHub, etc.
    """

    @abstractmethod
    def get_devices(self):
        """Returns all Meraki device inventory with tags, types, and overrides."""
        pass

    @abstractmethod
    def get_vlans(self):
        """Returns VLAN definitions, including subnet and DHCP settings."""
        pass

    @abstractmethod
    def get_firewall_rules(self):
        """Returns L3 firewall rules for both inbound and outbound."""
        pass

    @abstractmethod
    def get_static_routes(self):
        """Returns a list of static routes to be configured on the MX."""
        pass

    @abstractmethod
    def get_fixed_assignments(self):
        """Returns user-defined fixed IPs (non-Meraki devices, typically)."""
        pass

    @abstractmethod
    def get_exclusions(self):
        """Returns DHCP exclusions from the subnet pool for management IPs."""
        pass

    @abstractmethod
    def get_manifest(self):
        """Returns the high-level manifest mapping orgs and networks."""
        pass

    @abstractmethod
    def get_defaults(self):
        """Returns global defaults including naming and IPAM config."""
        pass
