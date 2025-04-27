# meraki_sdk/network/vlans/fixed_assignments.py
import yaml
import os

CONFIG_DIR = "config"


def load_fixed_assignments(yaml_path="fixed_ip_assignments.yaml"):
    """
    Load YAML file containing fixed IP assignments.

    Format expected:
    VLAN_NAME:
      MAC:
        ip: ...
        name: ...
        tags: [...]
    """
    full_path = os.path.join(CONFIG_DIR, yaml_path)
    if not os.path.exists(full_path):
        return {}  # No file = no fixed assignments

    with open(full_path, "r") as f:
        return yaml.safe_load(f) or {}


def get_vlan_fixed_assignments(vlan, fixed_assignments_data=None):
    """
    Given a VLAN, return the fixed IP assignments from YAML if present.
    
    Args:
    - vlan (dict): VLAN object (must contain 'name')
    - fixed_assignments_data (dict): optional preloaded assignments

    Returns:
    - dict of {MAC: {ip: ..., name: ..., tags: [...]}}
    """
    name = vlan.get("name", "Unnamed")

    if not fixed_assignments_data:
        fixed_assignments_data = load_fixed_assignments()

    return fixed_assignments_data.get(name, {})
