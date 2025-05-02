import os
import logging
from collections import Counter

logger = logging.getLogger(__name__)

def log_deployment_summary(config, org_name, named_devices, summary_filename=None):
    """
    Logs and saves a summary of the deployment.
    """
    logger.info("\U0001F4CA Summary of this deployment:")

    # Extract device types from structured device names (e.g., ...-MX-01)
    device_types = [device["name"].split("-")[-2] for device in named_devices]
    device_counter = Counter(device_types)

    logger.info(f"  1. \U0001F3E2 Organization '{org_name}' created.")
    logger.info(f"  2. \U0001F310 Network '{config['network']['name']}' created.")

    logger.info("  3. \U0001F4E6 Devices claimed:")
    for device_type, count in device_counter.items():
        logger.info(f"     - {count}x {device_type}")

    logger.info(f"  4. \U0001F3F7️ Devices named using template: {config['naming']['template']}")
    for device in named_devices:
        logger.info(f"     - {device['serial']} → {device['name']}")

    # Build summary lines
    summary_lines = []
    summary_lines.append("\n\U0001F4DC VLAN and DHCP Summary:")
    for vlan in config.get("vlans", []):
        summary_lines.append(f"    - VLAN {vlan.get('id')} ({vlan.get('name', 'Unnamed')}): {vlan.get('subnet')}")

    summary_lines.append("\n\U0001F4CC Fixed IP Assignments:")
    for vlan in config.get("vlans", []):
        vlan_id = vlan.get("id")
        name = vlan.get("name", "Unnamed VLAN")
        assignments = vlan.get("fixedIpAssignments", {})
        if assignments:
            summary_lines.append(f"    - VLAN {vlan_id} ({name}):")
            for mac, details in assignments.items():
                summary_lines.append(f"        {mac} → {details.get('ip')} ({details.get('name')})")
        else:
            summary_lines.append(f"    - VLAN {vlan_id} ({name}): No fixed IP assignments.")

    if config.get("static_routes"):
        summary_lines.append("\n\U0001F6A3️ Static Routes:")
        for route in config["static_routes"]:
            summary_lines.append(f"    - {route.get('name')}: {route.get('subnet')} via {route.get('gatewayIp', route.get('nextHopIp'))}")

    if config.get("firewall", {}).get("outbound_rules"):
        summary_lines.append("\n\U0001F6AA Outbound Firewall Rules:")
        for rule in config["firewall"]["outbound_rules"]:
            summary_lines.append(f"    - {rule.get('comment', 'Unnamed Rule')}")

    if config.get("firewall", {}).get("inbound_rules"):
        summary_lines.append("\n\U0001F6AA Inbound Firewall Rules:")
        for rule in config["firewall"]["inbound_rules"]:
            summary_lines.append(f"    - {rule.get('comment', 'Unnamed Rule')}")

    # Log all lines
    for line in summary_lines:
        logger.info(line)

    # Save to file using safe filename format
    summary_folder = "logs/summary_log"
    os.makedirs(summary_folder, exist_ok=True)

    if summary_filename is None:
        deployment_num = org_name.split()[-1]  # fallback logic
        summary_filename = f"summary-percystreet{deployment_num}.log"

    summary_path = os.path.join(summary_folder, summary_filename)
    with open(summary_path, "w") as f:
        for line in summary_lines:
            f.write(line + "\n")

    logger.info(f"\U0001F4DD Deployment summary saved to {summary_path}")
