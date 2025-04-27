# meraki_sdk/network/vlans/exclusions.py

import ipaddress
import math
import yaml
import os

CONFIG_DIR = "config"

def generate_exclusion_ranges(subnet_cidr, exclusion_ratio=0.25):
    """
    Auto-generate reserved IP ranges based on subnet size and exclusion ratio.

    Args:
    - subnet_cidr (str): CIDR block, e.g., "10.10.10.0/24"
    - exclusion_ratio (float): portion of usable IPs to reserve (default 25%)

    Returns:
    - List[dict]: [{start: ..., end: ..., comment: ...}]
    """
    network = ipaddress.IPv4Network(subnet_cidr, strict=False)
    hosts = list(network.hosts())

    if len(hosts) < 2:
        return []

    first_host = hosts[1]  # Start from .2
    num_hosts = len(hosts)
    num_to_reserve = max(1, math.floor(num_hosts * exclusion_ratio))
    last_reserved_host = hosts[1 + num_to_reserve - 1]

    return [{
        "start": str(first_host),
        "end": str(last_reserved_host),
        "comment": f"Auto-reserved {num_to_reserve} addresses ({exclusion_ratio*100:.0f}% of {num_hosts} usable)"
    }]

def load_exclusion_overrides(yaml_path="exclusion_rules.yaml"):
    """
    Load per-VLAN exclusion ratio overrides from YAML file.

    Args:
    - yaml_path (str): YAML filename relative to CONFIG_DIR.

    Returns:
    - dict: {vlan_name: exclusion_ratio}
    """
    full_path = os.path.join(CONFIG_DIR, yaml_path)
    if not os.path.exists(full_path):
        return {}

    with open(full_path, "r") as f:
        return yaml.safe_load(f) or {}

def get_vlan_exclusion(vlan, default_ratio=0.25, per_vlan_overrides=None):
    """
    Generate exclusion ranges for a VLAN.

    Args:
    - vlan (dict): VLAN object containing 'name' and 'subnet'
    - default_ratio (float): fallback exclusion ratio
    - per_vlan_overrides (dict): optional per-VLAN overrides

    Returns:
    - List[dict]: reserved IP ranges
    """
    name = vlan.get("name", "Unnamed")
    cidr = vlan.get("subnet")

    if not cidr:
        raise ValueError(f"VLAN '{name}' missing 'subnet' field")

    ratio = per_vlan_overrides.get(name, default_ratio) if per_vlan_overrides else default_ratio

    return generate_exclusion_ranges(cidr, exclusion_ratio=ratio)