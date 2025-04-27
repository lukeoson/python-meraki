# meraki_sdk/devices/mx_ports.py
import logging
from meraki.exceptions import APIError
import json

logger = logging.getLogger(__name__)

def configure_mx_ports(dashboard, network_id, config):
    """
    Configure MX ports using defaults and overrides from mx_ports.json
    """
    try:
        ports_config = config["mx_ports"]
        defaults = ports_config.get("defaults", {})
        custom_ports = {p["portId"]: p for p in ports_config.get("ports", [])}

        ports = dashboard.appliance.getNetworkAppliancePorts(network_id)
        logger.info(f"📥 Fetched {len(ports)} ports for network {network_id}.")

        for port in ports:
            port_number = port.get("number")
            if port_number is None:
                logger.warning(f"⚠️ Skipping a port without a number: {port}")
                continue

            # Merge default values + specific port overrides
            user_config = custom_ports.get(port_number, {})
            final_config = defaults.copy()
            final_config.update(user_config)

            payload = {}

            # Only set known supported fields
            if "name" in final_config:
                payload["name"] = final_config["name"]
            if "enabled" in final_config:
                payload["enabled"] = final_config["enabled"]
            if "type" in final_config:
                payload["type"] = final_config["type"]
            if "vlan" in final_config:
                payload["vlan"] = final_config["vlan"]
            if "allowedVlans" in final_config:
                if final_config.get("type") == "trunk":
                    payload["allowedVlans"] = final_config["allowedVlans"]
                else:
                    logger.debug(f"Skipping allowedVlans for port {port_number} (type={final_config.get('type')}) because it's not trunk.")

            if "dropUntaggedTraffic" in final_config:
                payload["dropUntaggedTraffic"] = final_config["dropUntaggedTraffic"]
            if "poeEnabled" in final_config:
                payload["poeEnabled"] = final_config["poeEnabled"]
            if "accessPolicy" in final_config:
                payload["accessPolicy"] = final_config["accessPolicy"]

            # WAN ports special case
            if payload.get("type") == "wan":
                allowed_fields = ["name", "enabled"]
                payload = {k: v for k, v in payload.items() if k in allowed_fields}

            if not payload:
                logger.warning(f"⚠️ No valid payload fields to configure port {port_number}. Skipping.")
                continue

            logger.info(f"🔌 Configuring Port {port_number}: {json.dumps(payload, indent=2)}")

            dashboard.appliance.updateNetworkAppliancePort(
                networkId=network_id,
                portId=port_number,
                **payload
            )

        logger.info("✅ MX ports configured successfully.")

    except APIError as e:
        logger.error(f"❌ API Error while configuring MX ports: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while configuring MX ports: {e}")