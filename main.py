import argparse
import json
import logging
import os
import re

from meraki_sdk.auth import get_dashboard_session
from meraki_sdk.org import get_previous_org
from meraki_sdk.network import ensure_network, get_next_network_by_prefix
from meraki_sdk.devices import (
    remove_devices_from_network,
    claim_devices,
    set_device_address,
)
from meraki_sdk.logging_config import setup_logging

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
    parser.add_argument("--config", default="config.json", help="Config file path")
    parser.add_argument("--api-key", default=os.getenv("MERAKI_API_KEY"), help="Meraki API key")
    parser.add_argument("--destroy", action="store_true", help="Remove devices from old network")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    dashboard = get_dashboard_session()

    # Fetch current orgs and determine next org name
    orgs = dashboard.organizations.getOrganizations()
    org_base_name = config["baseNames"]["organization"]
    net_base_name = config["baseNames"]["network"]
    org_name, _ = get_next_org_name_by_prefix(orgs, org_base_name)

    # Set up logging with dynamic log filename
    log_filename = f"py-meraki-{org_name.lower().replace(' ', '')}.log"
    setup_logging(log_filename)
    logger = logging.getLogger(__name__)

    # Create new org
    new_org = dashboard.organizations.createOrganization(name=org_name)
    org_id = new_org["id"]
    logger.info(f"✅ Created organization {org_name} ({org_id})")

    # Create new network
    config["network"]["name"] = f"{net_base_name} {org_name.split()[-1]}"
    network_id = ensure_network(dashboard, org_id, config["network"])
    logger.info(f"✅ Created network {config['network']['name']} ({network_id})")

    # Remove devices from previous network and clean up old org
    if args.destroy:
        previous_org = get_previous_org(orgs, org_base_name)
        if previous_org:
            previous_org_id = previous_org["id"]
            previous_org_name = previous_org["name"]
            previous_net = get_next_network_by_prefix(dashboard, previous_org_id, config["baseNames"]["network"])

            if previous_net:
                old_network_id = previous_net["id"]
                remove_devices_from_network(dashboard, old_network_id, config["devices"])
                dashboard.networks.deleteNetwork(old_network_id)
                logger.info(f"🗑️ Deleted old network '{previous_net['name']}' (ID: {old_network_id})")

            # Rename org to DEAD pattern using its original number
            match = re.search(r"(\d{3})$", previous_org_name)
            org_suffix = match.group(1) if match else "UNKNOWN"
            dead_name = f"DEAD - Delete old {org_suffix}"
            dashboard.organizations.updateOrganization(previous_org_id, name=dead_name)
            logger.info(f"⚰️ Renamed previous org '{previous_org_name}' → '{dead_name}'")
        else:
            logger.warning(f"⚠️  No valid previous {org_base_name} org to remove devices from.")

    # Prompt for manual unclaiming
    input("🔓 Not always needed. But please manually unclaim the devices from the previous org, then press Enter to continue...")

    # Claim devices to new network
    serials = [d["serial"] for d in config["devices"]]
    claim_devices(dashboard, network_id, serials)
    set_device_address(dashboard, serials)

    device_summary = "\n".join([
        f"     - {d['serial']} ({d['type']})" for d in config["devices"]
    ])

    logger.info("🏁 Workflow complete.")
    logger.info("\n📊 Summary of this deployment:")
    logger.info(f"  1. Organization '{org_name}' (ID: {org_id}) created.")
    logger.info(f"  2. Network '{config['network']['name']}' (ID: {network_id}) added to org.")
    logger.info(f"  3. Devices claimed:\n{device_summary}")

if __name__ == "__main__":
    main()
