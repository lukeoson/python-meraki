# meraki_sdk/network_constructs/ports/mx_ports.py
import logging
from meraki.exceptions import APIError
import json

logger = logging.getLogger(__name__)

def configure_mx_ports(dashboard, network_id, ports_config):
    """
    Configure MX ports using the provided `ports_config` dict,
    which should come from config["mx_ports"].
    """
    try:
        defaults     = ports_config.get("defaults", {})
        custom_ports = {p["portId"]: p for p in ports_config.get("ports", [])}

        ports = dashboard.appliance.getNetworkAppliancePorts(network_id)
        logger.info(f"📥 Fetched {len(ports)} ports for network {network_id}.")

        for port in ports:
            port_number = port.get("number")
            if port_number is None:
                logger.warning(f"⚠️ Skipping a port without a number: {port}")
                continue

            # Merge defaults + any per-port overrides
            override    = custom_ports.get(port_number, {})
            final_conf  = defaults.copy()
            final_conf.update(override)

            payload = {}
            # only set supported fields...
            if "name"               in final_conf: payload["name"]               = final_conf["name"]
            if "enabled"            in final_conf: payload["enabled"]            = final_conf["enabled"]
            if "type"               in final_conf: payload["type"]               = final_conf["type"]
            if "vlan"               in final_conf: payload["vlan"]               = final_conf["vlan"]
            if "allowedVlans"       in final_conf and final_conf.get("type") == "trunk":
                payload["allowedVlans"] = final_conf["allowedVlans"]
            if "dropUntaggedTraffic" in final_conf:
                payload["dropUntaggedTraffic"] = final_conf["dropUntaggedTraffic"]
            if "poeEnabled"         in final_conf: payload["poeEnabled"]         = final_conf["poeEnabled"]
            if "accessPolicy"       in final_conf: payload["accessPolicy"]       = final_conf["accessPolicy"]

            # WAN special: only name & enabled allowed
            if payload.get("type") == "wan":
                payload = {k: payload[k] for k in ("name","enabled") if k in payload}

            if not payload:
                logger.warning(f"⚠️ No fields to set on port {port_number}; skipping.")
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