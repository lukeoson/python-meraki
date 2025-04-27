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
    generate_device_names,
)
from meraki_sdk.devices import setup_devices
from meraki_sdk.network_constructs.setup_network_constructs import setup_network_constructs
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

    config = load_all_configs()
    dashboard = get_dashboard_session()

    orgs = dashboard.organizations.getOrganizations()
    org_base_name = config["base"]["baseNames"]["organization"]
    net_base_name = config["base"]["baseNames"]["network"]
    org_name, _ = get_next_org_name_by_prefix(orgs, org_base_name)

    # Setup logging
    log_filename = f"py-meraki-{org_name.lower().replace(' ', '')}.log"
    setup_logging(log_filename)
    logger = logging.getLogger(__name__)

    logger.info(f"Loaded config: {json.dumps(config, indent=2)}")

    # Create organization
    new_org = dashboard.organizations.createOrganization(name=org_name)
    org_id = new_org["id"]
    logger.info(f"✅ Created organization {org_name} ({org_id})")

    # Create network
    config["base"]["network"]["name"] = f"{net_base_name} {org_name.split()[-1]}"
    network_id = ensure_network(dashboard, org_id, config["base"]["network"])
    logger.info(f"✅ Created network {config['base']['network']['name']} ({network_id})")

    # Destroy old org if needed
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

    # 📦 Step 1: Setup devices (claim, address, names)
    named_devices = setup_devices(dashboard, network_id, config)

    # 🏗️ Step 2: Setup logical network constructs (VLANs, Static Routes, etc.)
    setup_network_constructs(dashboard, network_id, config)

    # 🔌 Step 3: Configure MX ports (now that VLANs are enabled)
    from meraki_sdk.network_constructs.ports.mx_ports import configure_mx_ports
    logger.info("🔌 Configuring MX ports…")
    configure_mx_ports(dashboard, network_id, config["mx_ports"])

    # 🏁 Step 4: Wrap up logging
    logger.info("🏁 Workflow complete.")
    logger.info("📊 Summary of this deployment:")

    # 1. Org and Network
    logger.info(f"  1. 🏢 Organization '{org_name}' created.")
    logger.info(f"  2. 🌐 Network '{config['base']['network']['name']}' created.")

    # 2. Devices claimed
    device_types = [d["type"] for d in config["devices"]["devices"]]
    counts = Counter(device_types)
    logger.info("  3. 📦 Devices claimed:")
    for t, cnt in counts.items():
        logger.info(f"     - {cnt}x {t}")

    # 3. Device naming
    logger.info(f"  4. 🏷️ Devices named using template: {config['base']['naming']['template']}")
    for d in named_devices:
        logger.info(f"     - {d['serial']} → {d['name']}")

    # 5. Static routes
    if config.get("static_routes"):
        logger.info("  5. 🛣️ Static routes created:")
        for r in config["static_routes"]:
            gw = r.get("gatewayIp", r.get("nextHopIp"))
            default = " (default gateway)" if r.get("defaultGateway") else ""
            logger.info(f"     - {r['name']}: {r['subnet']} via {gw}{default}")

    # Build the file summary
    summary_lines = []

    # VLAN & DHCP
    summary_lines.append("\n📜 VLAN and DHCP Summary:")
    for vlan in config["vlans"]:
        summary_lines.append(f"    - VLAN {vlan['id']} ({vlan.get('name','')}): {vlan['subnet']}")

    # Fixed IP assignments
    summary_lines.append("\n📌 Fixed IP Assignments:")
    for vlan in config["vlans"]:
        assigns = vlan.get("fixedIpAssignments", {})
        if assigns:
            summary_lines.append(f"    - VLAN {vlan['id']} ({vlan.get('name','')}):")
            for mac, info in assigns.items():
                summary_lines.append(f"        {mac} → {info['ip']} ({info.get('name','')})")
        else:
            summary_lines.append(f"    - VLAN {vlan['id']} ({vlan.get('name','')}): No fixed IPs.")

    # Static routes in file
    if config.get("static_routes"):
        summary_lines.append("\n🛣️ Static Routes:")
        for r in config["static_routes"]:
            gw = r.get("gatewayIp", r.get("nextHopIp"))
            default = " (default gateway)" if r.get("defaultGateway") else ""
            summary_lines.append(f"    - {r['name']}: {r['subnet']} via {gw}{default}")

    # Persist summary to disk using the org’s sequence as filename
    org_key = org_name.lower().replace(" ", "")  # e.g. "percystreet154"
    summary_folder = "logs/summary_log"
    os.makedirs(summary_folder, exist_ok=True)
    summary_file = os.path.join(
        summary_folder,
        f"deployment_summary_{org_key}.txt"
    )
    with open(summary_file, "w") as f:
        for line in summary_lines:
            f.write(line + "\n")

    logger.info(f"📝 Deployment summary saved to {summary_file}")

if __name__ == "__main__":
    main()