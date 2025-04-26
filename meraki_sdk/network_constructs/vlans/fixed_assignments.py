# meraki_sdk/network_constructs/vlans/fixed_assignments.py

import yaml
import os
import logging
import ipaddress

logger = logging.getLogger(__name__)
CONFIG_DIR = "config"

def load_fixed_assignments(yaml_path="config/fixed_ip_assignments.yaml"):
    """
    Load YAML file containing fixed IP assignments.
    Format:
    VLAN_NAME:
      MAC:
        ip: ...
        name: ...
        tags: [...]
    """
    full_path = os.path.join(CONFIG_DIR, yaml_path)
    if not os.path.isfile(full_path):
        logger.debug(f"No fixed assignments file found at {full_path}")
        return {}

    with open(full_path, "r") as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {full_path}: {e}")
            return {}

def get_vlan_fixed_assignments(vlan, fixed_assignments_data=None):
    """
    Get fixed IP assignments for a VLAN by its name.
    """
    if not vlan or "name" not in vlan:
        logger.warning("VLAN data missing 'name' field.")
        return {}

    fixed_assignments_data = fixed_assignments_data or load_fixed_assignments()
    return fixed_assignments_data.get(vlan["name"], {})

def auto_generate_fixed_assignments_for_vlan_10(dashboard, network_id, vlan, starting_ip="10.10.10.100"):
    if not vlan or vlan.get("id") != 10:
        return

    fixed_assignments = vlan.get("fixedIpAssignments", {})
    used_ips = {ip["ip"] for ip in fixed_assignments.values()}

    subnet = ipaddress.IPv4Network(vlan.get("subnet", "10.10.10.0/24"))
    ip_gen = (str(ip) for ip in subnet.hosts() if str(ip) not in used_ips and int(ip.packed[-1]) >= 100)

    try:
        devices = dashboard.networks.getNetworkDevices(network_id)
    except Exception as e:
        logger.error(f"Failed to retrieve devices: {e}")
        return

    for device in devices:
        mac = device.get("mac")
        model = device.get("model", "")
        if not mac:
            continue

        try:
            assigned_ip = next(ip_gen)
        except StopIteration:
            logger.error(f"Ran out of IPs in {subnet}!")
            break

        fixed_assignments[mac] = {
            "ip": assigned_ip,
            "name": device.get("name", "Auto-assigned device"),
            "tags": ["MGMT", "auto-fixed"]
        }
        logger.debug(f"Assigned {mac} ({model}) → {assigned_ip}")

    vlan["fixedIpAssignments"] = fixed_assignments