import argparse
import logging
import os
from meraki_sdk.auth import get_dashboard_session
from meraki_sdk.basic_network import ensure_network
from meraki_sdk.device import remove_devices_from_network
from meraki_sdk.devices import setup_devices
from meraki_sdk.network.setup_network import setup_network
from meraki_sdk.logging_config import setup_logging
from meraki_sdk.logging.summary import log_deployment_summary
from config_resolver import resolve_project_configs

# 💾 Use new backend abstraction layer
from backend.local_yaml_backend import LocalYAMLBackend


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", default=os.getenv("MERAKI_API_KEY"), help="Meraki API key")
    parser.add_argument("--destroy", action="store_true", help="Remove devices from previous orgs")
    parser.add_argument("--tag", help="Deploy a single tag (org-network pair)")
    args = parser.parse_args()

    # 🪵 Logging and Meraki session
    setup_logging("py-meraki.log")
    logger = logging.getLogger(__name__)
    dashboard = get_dashboard_session()

    # 🧠 Use backend abstraction to load configs
    backend = LocalYAMLBackend()
    manifest = backend.get_manifest()
    defaults = backend.get_defaults()
    all_devices = backend.get_devices()["groups"]  # Top-level key expected

    # ⚙️ Resolve configs (merge defaults, apply overrides)
    config_data = resolve_project_configs(backend=backend)
    resolved_networks = config_data["resolved_networks"]

    # 🔁 Group networks by project/org_base_name
    grouped = {}
    for entry in resolved_networks:
        grouped.setdefault(entry["org_base_name"], []).append(entry)

    # 🚀 Deploy each project/org
    for org_base, networks in grouped.items():
        project_name = networks[0]["project_name"]

        # 🏢 Get existing orgs and generate new org name
        orgs = dashboard.organizations.getOrganizations()
        existing = [o for o in orgs if o["name"].startswith(org_base)]
        org_suffix = f"{len(existing):03d}"
        org_name = f"{org_base} {org_suffix}"
        new_org = dashboard.organizations.createOrganization(name=org_name)
        org_id = new_org["id"]

        # 🔥 Cleanup old orgs
        if args.destroy:
            previous = existing[-1] if existing else None
            if previous:
                prev_org_id = previous["id"]
                logger.info(f"🔍 Cleaning up previous org: {previous['name']} ({prev_org_id})")
                try:
                    prev_nets = dashboard.organizations.getOrganizationNetworks(prev_org_id)
                    for net in prev_nets:
                        logger.info(f"🗑️ Removing devices from network: {net['name']}")
                        remove_devices_from_network(dashboard, net["id"], all_devices)
                        dashboard.networks.deleteNetwork(net["id"])
                        logger.info(f"✅ Deleted network: {net['name']}")
                except Exception as e:
                    logger.error(f"❌ Error deleting networks from old org: {e}")
                try:
                    dead_name = f"DEAD - Delete old {previous['name']}"
                    dashboard.organizations.updateOrganization(organizationId=prev_org_id, name=dead_name)
                    logger.info(f"⚰️ Renamed old org to: {dead_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to rename old org: {e}")

        # 🌐 Deploy all networks inside the new org
        for entry in networks:
            tag = entry["full_tag"]
            if args.tag and args.tag != tag:
                continue

            net_base = entry["net_base_name"]
            config = entry["network_config"]
            logger.info(f"🚀 Starting deployment for: {project_name} / {tag}")

            net_name = f"{net_base} {org_suffix}"
            config["network"]["name"] = net_name
            network_id = ensure_network(dashboard, org_id, config["network"])
            config["base"] = entry.get("base", {})

            # Flatten devices and inherit group-level tags
            flat_devices = []
            for group in all_devices:
                group_tag = group.get("tag")
                for device in group.get("devices", []):
                    device_tags = device.get("tags", [])
                    if isinstance(device_tags, str):
                        device_tags = [device_tags]
                    device["tags"] = list(set(device_tags + [group_tag]))
                    flat_devices.append(device)
            
            # Normalize tag comparison (handle underscores/hyphens)
            def normalize(s):
                return s.replace("_", "-")
            
            tagged_devices = [
                d for d in flat_devices
                if normalize(tag) in [normalize(t) for t in d.get("tags", [])]
            ]
            
            if not tagged_devices:
                raise ValueError(f"No devices found for tag '{tag}'. Check your devices.yaml.")

            named_devices = setup_devices(dashboard, network_id, {
                "devices": tagged_devices,
                "base": config
            })

            setup_network(dashboard, network_id, config)
            log_deployment_summary(config, org_name, named_devices)
            logger.info(f"✅ Deployment for {org_name} complete.")


if __name__ == "__main__":
    main()
