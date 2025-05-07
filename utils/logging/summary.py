deployment_summaries = []
import os
import logging
from collections import Counter
import json

logger = logging.getLogger(__name__)

def log_deployment_summary(config, org_name, named_devices, dashboard, summary_filename=None):
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

    # Live API Verification Summary
    summary_lines.append("\n🔍 Live API Verification Summary:")

    try:
        network_id = config["network_id"]
        live_network = dashboard.networks.getNetwork(network_id)
        summary_lines.append(f"    - ✅ Network exists: {live_network['name']}")
    except Exception as e:
        summary_lines.append(f"    - ❌ Network verification failed: {str(e)}")

    try:
        live_vlans = dashboard.appliance.getNetworkApplianceVlans(network_id)
        summary_lines.append(f"    - ✅ Found {len(live_vlans)} VLANs on network.")
    except Exception as e:
        summary_lines.append(f"    - ❌ VLANs verification failed: {str(e)}")

    try:
        live_ssids = dashboard.wireless.getNetworkWirelessSsids(network_id)
        summary_lines.append(f"    - ✅ Found {len(live_ssids)} Wireless SSIDs.")
    except Exception as e:
        summary_lines.append(f"    - ❌ Wireless SSIDs verification failed: {str(e)}")

    # ======= Structured, user-readable summaries for each category =======
    summary_lines.append("\n📡 Verified Configuration Overview:")

    # Org and Network
    summary_lines.append(f"    - ✅ Organization: {org_name}")
    summary_lines.append(f"    - ✅ Network Name: {config['network']['name']}")
    summary_lines.append(f"    - ✅ Network ID: {config.get('network_id', '❌ Not Found')}")

    # Location Info
    locations = set((d.get("address") for d in named_devices if d.get("address")))
    if locations:
        summary_lines.append("    - 📍 Location(s):")
        for loc in locations:
            summary_lines.append(f"        • {loc}")
    else:
        summary_lines.append("    - 📍 No location info available.")

    # VLANs
    summary_lines.append("    - 🌐 VLANs:")
    for vlan in config.get("vlans", []):
        summary_lines.append(f"        • VLAN {vlan['id']} '{vlan['name']}' → {vlan['subnet']}")

    # Ports
    summary_lines.append("    - 🔌 MX Ports:")
    for port in config.get("mx_ports", {}).get("ports", []):
        summary_lines.append(f"        • Port {port['portId']} → VLAN {port.get('vlan', 'N/A')} ({port['type']})")

    # Static Routes
    summary_lines.append("    - 🛣️ Static Routes:")
    for route in config.get("mx_static_routes", []):
        summary_lines.append(f"        • {route['name']} → {route['subnet']} via {route['gatewayIp']}")

    # Firewall Rules
    fw = config.get("firewall", {})
    summary_lines.append("    - 🔥 Firewall Rules:")
    if fw.get("inbound_rules"):
        summary_lines.append("        • Inbound:")
        for rule in fw["inbound_rules"]:
            summary_lines.append(f"            - {rule.get('comment', 'Unnamed')}")
    else:
        summary_lines.append("        • Inbound: None")
    if fw.get("outbound_rules"):
        summary_lines.append("        • Outbound:")
        for rule in fw["outbound_rules"]:
            summary_lines.append(f"            - {rule.get('comment', 'Unnamed')}")
    else:
        summary_lines.append("        • Outbound: None")

    # Wireless SSIDs
    ssids = config.get("mx_wireless", {}).get("ssids", [])
    summary_lines.append("    - 📶 Wireless SSIDs:")
    if ssids:
        for ssid in ssids:
            summary_lines.append(f"        • {ssid['name']} (VLAN {ssid.get('defaultVlanId')})")
    else:
        summary_lines.append("        • None configured")

    # Devices
    summary_lines.append("    - 📦 Devices Claimed and Named:")
    for device in named_devices:
        summary_lines.append(f"        • {device['model']} {device['name']} — {device['serial']}")

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

    # Save summary as JSON
    json_summary_path = os.path.join(summary_folder, summary_filename.replace(".log", ".json"))
    with open(json_summary_path, "w") as jf:
        json.dump({
            "organization": org_name,
            "network": config.get("network", {}).get("name"),
            "named_devices": named_devices,
            "summary_lines": summary_lines
        }, jf, indent=2)
    logger.info(f"\U0001F4BE JSON summary saved to {json_summary_path}")

    logger.info(f"\U0001F4DD Deployment summary saved to {summary_path}")


# === Deployment summary collection and printing ===

def collect_deployment_summary(config, org_name, named_devices, summary_lines):
    deployment_summaries.append({
        "organization": org_name,
        "network": config.get("network", {}).get("name", "Unknown Network"),
        "summary_lines": summary_lines
    })

def print_final_summary():
    logger.info("\n📋 FINAL DEPLOYMENT SUMMARY")
    for idx, entry in enumerate(deployment_summaries, 1):
        logger.info(f"\n🔹 Deployment {idx}: {entry['organization']} / {entry['network']}")
        for line in entry["summary_lines"]:
            logger.info(line)
