import argparse
import json
import logging
import os
import re

from meraki_sdk.auth import get_dashboard_session
from meraki_sdk.org import get_previous_percy_org
from meraki_sdk.network import ensure_network, get_studio_lab_network
from meraki_sdk.devices import (
    remove_devices_from_network,
    claim_devices,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_next_sequence_name(items, base_name):
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
    org_name, _ = get_next_sequence_name(orgs, "Percy Street")

    # Create new org
    new_org = dashboard.organizations.createOrganization(name=org_name)
    org_id = new_org["id"]
    logger.info(f"✅ Created organization {org_name} ({org_id})")

    # Create new network
    config["network"]["name"] = f"Studio Lab {org_name.split()[-1]}"
    network_id = ensure_network(dashboard, org_id, config["network"])
    logger.info(f"✅ Created network {config['network']['name']} ({network_id})")

    # Remove devices from previous network
    if args.destroy:
        previous_org = get_previous_percy_org(orgs)
        if previous_org:
            previous_org_id = previous_org["id"]
            previous_net = get_studio_lab_network(dashboard, previous_org_id)
            if previous_net:
                old_network_id = previous_net["id"]
                remove_devices_from_network(dashboard, old_network_id, config["devices"])
            else:
                logger.warning("⚠️  No previous Studio Lab network found in previous org.")
        else:
            logger.warning("⚠️  No valid previous Percy Street org to remove devices from.")

    # Prompt for manual unclaiming
    input("🔓 Please manually unclaim the devices from the previous org, then press Enter to continue...")

    # Claim devices to new network
    serials = [d["serial"] for d in config["devices"]]
    claim_devices(dashboard, network_id, serials)

    ## Optional: bind sensors to MV72 - didnt work tried for hours. LR
    #mv_serial = next((d["serial"] for d in config["devices"] if d["type"] == "MV"), None)
    #sensor_serials = [d["serial"] for d in config["devices"] if d["type"].startswith("MT")]
    #if mv_serial and sensor_serials:
    #    bind_sensors_to_camera(dashboard, network_id, mv_serial, sensor_serials)

    logger.info("🏁 Workflow complete.")

if __name__ == "__main__":
    main()

