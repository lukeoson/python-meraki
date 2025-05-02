import os
import logging
from collections import Counter

logger = logging.getLogger(__name__)

def log_deployment_summary(config, org_name, named_devices):
    """
    Logs and saves a summary of the deployment.
    """
    logger.info("📊 Summary of this deployment:")

    # Extract device types from structured device names (e.g., ...-MX-01)
    device_types = [device["name"].split("-")[-2] for device in named_devices]
    device_counter = Counter(device_types)

    logger.info(f"  1. 🏢 Organization '{org_name}' created.")
    logger.info(f"  2. 🌐 Network '{config['network']['name']}' created.")

    logger.info("  3. 📦 Devices claimed:")
    for device_type, count in device_counter.items():
        logger.info(f"     - {count}x {device_type}")

    logger.info(f"  4. 🏷️ Devices named using template: {config['naming']['template']}")
    for device in named_devices:
        logger.info(f"     - {device['serial']} → {device['name']}")

    # Build summary lines
    summary_lines = []
    summary_lines.append("\n📜 VLAN and DHCP Summary:")
    for vlan in config.get("vlans", []):
        summary_lines.append(f"    - VLAN {vlan.get('id')} ({vlan.get('name', 'Unnamed')}): {vlan.get('subnet')}")

    summary_lines.append("\n📌 Fixed IP Assignments:")
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
        summary_lines.append("\n🛣️ Static Routes:")
        for route in config["static_routes"]:
            summary_lines.append(f"    - {route.get('name')}: {route.get('subnet')} via {route.get('gatewayIp', route.get('nextHopIp'))}")

    if config.get("firewall", {}).get("outbound_rules"):
        summary_lines.append("\n🚪 Outbound Firewall Rules:")
        for rule in config["firewall"]["outbound_rules"]:
            summary_lines.append(f"    - {rule.get('comment', 'Unnamed Rule')}")

    if config.get("firewall", {}).get("inbound_rules"):
        summary_lines.append("\n🚪 Inbound Firewall Rules:")
        for rule in config["firewall"]["inbound_rules"]:
            summary_lines.append(f"    - {rule.get('comment', 'Unnamed Rule')}")

    # Log all lines
    for line in summary_lines:
        logger.info(line)

    # Save to file using org_name-based filename
    deployment_num = org_name.split()[-1]  # example: 'Percy Street 155' → 155
    summary_folder = "logs/summary_log"
    os.makedirs(summary_folder, exist_ok=True)
    summary_file = os.path.join(summary_folder, f"deployment_summary_percystreet{deployment_num}.txt")

    with open(summary_file, "w") as f:
        for line in summary_lines:
            f.write(line + "\n")

    logger.info(f"📝 Deployment summary saved to {summary_file}")