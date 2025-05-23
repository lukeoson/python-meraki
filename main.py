import argparse
import logging
import os
from utils.logging.config import setup_logging
from utils.logging.summary import log_deployment_summary
from utils.logging.summary import collect_deployment_summary, print_final_summary
from utils.state.config import save_intended_state
from utils.state.runtime import save_runtime_state
from meraki_sdk.auth import get_dashboard_session
from meraki_sdk.basic_network import ensure_network
from meraki_sdk.device import remove_devices_from_network
from meraki_sdk.devices import setup_devices
from meraki_sdk.network.setup_network import setup_network
from meraki_sdk.org import get_next_sequence_name, get_previous_org
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
    logger = logging.getLogger(__name__)
    # ✅ Setup Meraki session (Meraki logs will use default naming with timestamps)
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

    all_summaries = []

    # 🚀 Deploy each project/org
    for org_base, networks in grouped.items():
        project_name = networks[0]["project_name"]

        # 🔧 Initialize runtime state for this org
        runtime_state = {
            "project_slug": project_name,
            "org": {
                "org_id": None,
                "org_name": None
            },
            "networks": {}
        }

        # 🏢 Get all orgs and determine next available name
        orgs = dashboard.organizations.getOrganizations()
        org_name, next_seq = get_next_sequence_name(orgs, org_base)
        new_org = dashboard.organizations.createOrganization(name=org_name)
        org_id = new_org["id"]

        runtime_state["org"]["org_id"] = org_id
        runtime_state["org"]["org_name"] = org_name

        # ✅ Set up org-specific logging
        log_safe_name = org_name.lower().replace(" ", "").replace("-", "")
        custom_log_name = f"custom-{log_safe_name}.log"
        setup_logging(custom_log_name)
        logger = logging.getLogger(__name__)

        # 🔥 Cleanup old orgs
        if args.destroy:
            previous = get_previous_org(orgs, org_base)
            if previous:
                prev_org_id = previous["id"]
                logger.info(f"🔍 Cleaning up previous org: {previous['name']} ({prev_org_id})")

                try:
                    prev_nets = dashboard.organizations.getOrganizationNetworks(prev_org_id)
                    for net in prev_nets:
                        logger.info(f"🗑️ Cleaning up network: {net['name']}")

                        # 🔍 Get all devices in this network
                        devices_in_net = dashboard.networks.getNetworkDevices(net["id"])

                        # 🚫 Remove devices
                        remove_devices_from_network(dashboard, net["id"], devices_in_net)

                        # 🗑️ Delete network
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

            net_name = f"{net_base} {next_seq:03d}"
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

            # Inject wireless context for MX68CW support
            config["named_devices"] = named_devices
            config["project_name"] = project_name

            # 💾 Accumulate runtime state for this network
            runtime_state["networks"][entry["network_slug"]] = {
                "network_id": network_id,
                "network_name": config["network"]["name"]
            }
            # Store org_id and network_id in config for later retrieval/logging
            config["org_id"] = org_id
            config["network_id"] = network_id

            save_runtime_state(
                runtime_state["project_slug"],
                runtime_state["org"]["org_id"],
                runtime_state["org"]["org_name"],
                runtime_state["networks"]
            )

            # 🧠 Resolve hubId for AutoVPN spoke configs
            if "mx_autovpn" in config and config["mx_autovpn"].get("mode") == "spoke":
                for hub in config["mx_autovpn"].get("hubs", []):
                    if hub.get("hubId") == "TBD":
                        hub_slug = config.get("mx_autovpn", {}).get("hub_slug", "studio_hub")
                        resolved_hub_id = runtime_state["networks"].get(hub_slug, {}).get("network_id")
                        logger.info(f"🔁 Resolving hubId for spoke VPN config: {hub_slug} -> {resolved_hub_id}")
                        hub["hubId"] = resolved_hub_id

            setup_network(dashboard, network_id, config)

            # 📝 Save summary and full intended state for audit/debugging
            log_safe_name = org_name.lower().replace(" ", "").replace("-", "")
            summary_log_name = f"summary-{log_safe_name}.log"
            summary_lines = [
                f"🔹 Network: {config['network']['name']}",
                f"🌍 Org: {org_name}",
                f"📦 Devices: {len(named_devices)} device(s) configured"
            ]
            collect_deployment_summary(config, org_name, named_devices, summary_lines)
            log_deployment_summary(config, org_name, named_devices, dashboard, summary_log_name)

            # 💾 Save intended state (JSON representation of this config)
            state_path = save_intended_state(config, org_name)
            logger.info(f"📦 Intended state saved to {state_path}")

            logger.info(f"✅ Deployment for {org_name} complete.")

    print_final_summary()


if __name__ == "__main__":
    main()
