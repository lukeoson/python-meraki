deployment_summaries = {}
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

    summary_folder = "logs/summary_log"
    os.makedirs(summary_folder, exist_ok=True)

    if summary_filename is None:
        safe_org = org_name.lower().replace(" ", "").replace("-", "")
        summary_filename = f"summary-{safe_org}.log"

    summary_path = os.path.join(summary_folder, summary_filename)

    if not os.path.exists(summary_path):
        header_lines = [
            f"\n🧾 This file contains a full summary of the deployment actions taken for the Meraki organization '{org_name}'.",
            f"   It includes configuration steps, device mappings, API verification checks, and VLAN/subnet information.",
            f"\n🌍 Organization: {org_name}",
            f"🏢 Networks in this organization will be listed below as they are deployed.",
            "\n"
        ]
        with open(summary_path, "a") as f:
            for line in header_lines:
                f.write(line + "\n")

    # ======= Structured, user-readable summaries for each category =======
    summary_lines = []

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

    # Devices
    summary_lines.append("    - 📦 Devices Claimed and Named:")
    for device in named_devices:
        summary_lines.append(f"        • {device['model']} {device['name']} — {device['serial']}")

    # Ports
    summary_lines.append("    - 🔌 MX Ports:")
    for port in config.get("mx_ports", {}).get("ports", []):
        summary_lines.append(f"        • Port {port['portId']} → VLAN {port.get('vlan', 'N/A')} ({port['type']})")

    # VLANs
    summary_lines.append("    - 🌐 VLANs:")
    for vlan in config.get("vlans", []):
        summary_lines.append(f"        • VLAN {vlan['id']} '{vlan['name']}' → {vlan['subnet']}")

    # Fixed Assignments
    summary_lines.append("    - 📌 Fixed IP Assignments:")
    for vlan in config.get("vlans", []):
        vlan_id = vlan.get("id")
        name = vlan.get("name", "Unnamed VLAN")
        assignments = vlan.get("fixedIpAssignments", {})
        if assignments:
            summary_lines.append(f"        • VLAN {vlan_id} ({name}):")
            for mac, details in assignments.items():
                summary_lines.append(f"            - {mac} → {details.get('ip')} ({details.get('name')})")
        else:
            summary_lines.append(f"        • VLAN {vlan_id} ({name}): No fixed IP assignments.")

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

    # Insert network header line before verified configuration overview
    summary_lines.insert(0, f"\n📡 Network: {config['network']['name']} — Deployment Summary Begins")
    summary_lines.append("")  # adds a blank line

    summary_lines.append(f"\n✅ End of configuration summary for network '{config['network']['name']}'")

    # Log all lines
    for line in summary_lines:
        logger.info(line)

    # Save to file using safe filename format
    # Append to the summary file for the same org instead of overwriting
    with open(summary_path, "a") as f:
        for line in summary_lines:
            f.write(line + "\n")

    # Save summary as JSON, appending new networks under each org
    json_summary_path = os.path.join(summary_folder, summary_filename.replace(".log", ".json"))
    # Try to load existing JSON, if present
    if os.path.exists(json_summary_path):
        try:
            with open(json_summary_path, "r") as jf:
                existing = json.load(jf)
        except Exception:
            existing = {}
    else:
        existing = {}
    # Ensure structure: { "organization": org_name, "networks": [ ... ] }
    if not existing or existing.get("organization") != org_name:
        existing = {
            "organization": org_name,
            "networks": []
        }
    existing["networks"].append({
        "network": config.get("network", {}).get("name"),
        "named_devices": named_devices,
        "summary_lines": summary_lines
    })
    with open(json_summary_path, "w") as jf:
        json.dump(existing, jf, indent=2)
    logger.info(f"\U0001F4BE JSON summary saved to {json_summary_path}")

    logger.info(f"\U0001F4DD Deployment summary saved to {summary_path}")


# === Deployment summary collection and printing ===

def collect_deployment_summary(config, org_name, named_devices, summary_lines):
    if org_name not in deployment_summaries:
        deployment_summaries[org_name] = []
    deployment_summaries[org_name].append({
        "network": config.get("network", {}).get("name", "Unknown Network"),
        "org_id": config.get("org_id", "❌ Not Provided"),
        "network_id": config.get("network_id", "❌ Not Provided"),
        "device_count": len(named_devices),
        "summary_lines": summary_lines
    })

def print_final_summary():
    logger.info("📋 FINAL DEPLOYMENT SUMMARY\n")
    logger.info("=" * 50)

    for org_name, networks in deployment_summaries.items():
        logger.info(f"🌍 Organization: {org_name}")
        logger.info(f"🏢 {len(networks)} network(s) deployed:\n")
        network_list_str = " & ".join([f"{i+1}: {n['network']}" for i, n in enumerate(networks)])
        logger.info(f"📋 Networks Deployed: {network_list_str}\n")

        for idx, entry in enumerate(networks, 1):
            logger.info(f"🔹 Network: {entry['network']}")
            logger.info(f"🌍 Org: {org_name}")
            logger.info(f"🆔 Org ID: {entry.get('org_id', '❌ Not Provided')}")
            logger.info(f"🆔 Network ID: {entry.get('network_id', '❌ Not Provided')}")
            logger.info(f"📦 Devices: {entry.get('device_count', '0')} device(s) configured")
            logger.info("-" * 50)
            logger.info("")  # Blank line between networks
