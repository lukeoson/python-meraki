import argparse
import json
import logging
import os
import re
from datetime import datetime
from collections import Counter

from meraki_sdk.auth import get_dashboard_session
from meraki_sdk.org import get_previous_org
from meraki_sdk.network import ensure_network, get_next_network_by_prefix
from meraki_sdk.device import (
    remove_devices_from_network,
    claim_devices,
    set_device_address,
    set_device_names,
    generate_device_names
)
from meraki_sdk.network_constructs.vlans import configure_mx_vlans
from meraki_sdk.devices import configure_mx_ports, setup_devices
from meraki_sdk.logging_config import setup_logging
from config_loader import load_all_configs

def get_next_org_name_by_prefix(items, base_name):
    pattern = re.compile(rf"{re.escape(base_name)} (\d+)")
    numbers = [
        int(m.group(1)) for item in items
        if (m := pattern.search(item['name']))
    ]
    next_seq = max(numbers, default=-1) + 1
    return f"{base_name} {next_seq:03d}", next_seq

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", default=os.getenv("MERAKI_API_KEY"), help="Meraki API key")
    parser.add_argument("--destroy", action="store_true", help="Remove devices from old network")
    args = parser.parse_args()

    # Load configuration files
    config = load_all_configs()

    dashboard = get_dashboard_session()

    # Fetch current orgs and determine next org name
    orgs = dashboard.organizations.getOrganizations()
    org_base_name = config["base"]["baseNames"]["organization"]
    net_base_name = config["base"]["baseNames"]["network"]
    org_name, _ = get_next_org_name_by_prefix(orgs, org_base_name)

    # Set up logging with dynamic log filename
    log_filename = f"py-meraki-{org_name.lower().replace(' ', '')}.log"
    setup_logging(log_filename)
    logger = logging.getLogger(__name__)

    logger.info(f"Loaded config: {json.dumps(config, indent=2)}")

    # Create new organization
    new_org = dashboard.organizations.createOrganization(name=org_name)
    org_id = new_org["id"]
    logger.info(f"✅ Created organization {org_name} ({org_id})")

    # Create new network
    config["base"]["network"]["name"] = f"{net_base_name} {org_name.split()[-1]}"
    network_id = ensure_network(dashboard, org_id, config["base"]["network"])
    logger.info(f"✅ Created network {config['base']['network']['name']} ({network_id})")

    # Remove devices from previous network and clean up old org
    if args.destroy:
        previous_org = get_previous_org(orgs, org_base_name)
        if previous_org:
            previous_org_id = previous_org["id"]
            previous_org_name = previous_org["name"]
            previous_net = get_next_network_by_prefix(dashboard, previous_org_id, config["base"]["baseNames"]["network"])

            if previous_net:
                old_network_id = previous_net["id"]
                remove_devices_from_network(dashboard, old_network_id, config["devices"]["devices"])
                dashboard.networks.deleteNetwork(old_network_id)
                logger.info(f"🗑️ Deleted old network '{previous_net['name']}' (ID: {old_network_id})")

            match = re.search(r"(\d{3})$", previous_org_name)
            org_suffix = match.group(1) if match else "UNKNOWN"
            dead_name = f"DEAD - Delete old {org_suffix}"
            dashboard.organizations.updateOrganization(previous_org_id, name=dead_name)
            logger.info(f"⚰️ Renamed previous org '{previous_org_name}' → '{dead_name}'")
        else:
            logger.warning(f"⚠️ No valid previous {org_base_name} org to remove devices from.")

    # Claim devices to new network
    serials = [d["serial"] for d in config["devices"]["devices"]]
    claim_devices(dashboard, network_id, serials)

    # 📦 NEW REFACTOR: Clean post-claim setup
    setup_devices(dashboard, network_id, config)

    # Wrap up
    device_summary = "\n".join([
        f"     - {d['serial']} ({d['type']})" for d in config["devices"]["devices"]
    ])

    # Log the summary of the deployment
    logger.info("🏁 Workflow complete.")
    logger.info("📊 Summary of this deployment:")

    summary_lines = []
    
    logger.info(f"  1. 🏢 Organization '{org_name}' (ID: {org_id}) created.")
    logger.info(f"  2. 🌐 Network '{config['base']['network']['name']}' (ID: {network_id}) added to org.")

    # Group claimed devices by type
    device_types = [device["type"] for device in config["devices"]["devices"]]
    device_counter = Counter(device_types)

    logger.info(f"  3. 📦 Devices claimed:")
    for device_type, count in device_counter.items():
        logger.info(f"     - {count}x {device_type}")

    # Named devices with template
    logger.info(f"  4. 🏷️ Devices named using template: {config['base']['naming']['template']}")
    generated_devices = generate_device_names(
        config["devices"]["devices"],
        config["base"]["naming"]
        )
    for device in generated_devices:
        logger.info(f"     - {device['serial']} → {device['name']}")

    # VLANs
    logger.info(f"  5. 🌐 VLANs configured: {len(config['vlans'])} VLANs applied.")

    # Ports
    logger.info(f"  6. 🔌 MX ports configured: {len(config['mx_ports']['ports'])} custom + {len(config['mx_ports'].get('defaults', {}))} defaults.")

    # Manual step
    logger.info(f"  7. ⚰️ Manual step: delete org '{dead_name}' if needed.")

    # Light touch: only decorate MAJOR sections
    def colorize(text, color_code):
        return f"\033[{color_code}m{text}\033[0m"

    # 8. VLAN and DHCP Summary
    summary_lines.append(colorize("  8. 📜 VLAN and DHCP Configuration:", "96"))  # Cyan header
    for vlan in config["vlans"]:
        vlan_id = vlan.get("id")
        name = vlan.get("name", "Unnamed VLAN")
        subnet = vlan.get("subnet", "Unknown Subnet")
        gateway = vlan.get("gatewayIp", "Unknown Gateway")
        reserved_ranges = vlan.get("reservedIpRanges", [])
        exclusions = [f"{r['start']}–{r['end']}" for r in reserved_ranges] if reserved_ranges else ["None"]

        summary_lines.append(f"    - VLAN {vlan_id} ({name}): {subnet}, Gateway: {gateway}")
        summary_lines.append(f"      Reserved IPs: {', '.join(exclusions)}")

    # 9. Fixed IP Assignments
    summary_lines.append(colorize("  9. 📌 Fixed IP Assignments:", "93"))  # Yellow header
    for vlan in config["vlans"]:
        vlan_id = vlan.get("id")
        name = vlan.get("name", "Unnamed VLAN")
        assignments = vlan.get("fixedIpAssignments", {})
        if assignments:
            summary_lines.append(f"    - VLAN {vlan_id} ({name}):")
            for mac, details in assignments.items():
                ip = details.get("ip", "Unknown IP")
                device_name = details.get("name", "Unnamed Device")
                summary_lines.append(f"        {mac} → {ip} ({device_name})")
        else:
            summary_lines.append(f"    - VLAN {vlan_id} ({name}): No fixed IP assignments.")

    # 10. Deployment finished
    summary_lines.append(colorize(" 10. 🎩 Deployment finished successfully.", "92"))  # Green header

    # Print summary to console
    for line in summary_lines:
        logger.info(line)

    # Save plain text summary
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_folder = "logs/summary_log"
    os.makedirs(summary_folder, exist_ok=True)
    summary_file = os.path.join(summary_folder, f"deployment_summary_{timestamp}.txt")
    with open(summary_file, "w") as f:
        for line in summary_lines:
            # Strip ANSI escape codes only for saving
            plain_line = line.replace("\033[96m", "").replace("\033[93m", "").replace("\033[92m", "").replace("\033[0m", "")
            f.write(plain_line + "\n")

    logger.info(f"📝 Deployment summary saved to {summary_file}")


if __name__ == "__main__":
    main()
