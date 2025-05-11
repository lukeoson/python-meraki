# meraki_sdk/network/ports/mx_ports.py
import logging
from meraki.exceptions import APIError
import json

logger = logging.getLogger(__name__)

def configure_mx_ports(dashboard, network_id, ports_config):
    """
    Configure MX ports using the provided `ports_config` list.
    Each item should be a dict containing a fully resolved port configuration.
    """
    try:
        if not isinstance(ports_config, list):
            logger.error(f"❌ Expected mx_ports to be a list, got {type(ports_config).__name__}")
            return

        ports = dashboard.appliance.getNetworkAppliancePorts(network_id)
        logger.info(f"📥 Fetched {len(ports)} ports for network {network_id}.")

        # Index provided config by portId for fast lookup
        override_ports = {str(p["portId"]): p for p in ports_config if "portId" in p}

        for port in ports:
            port_number = str(port.get("number"))
            if port_number not in override_ports:
                logger.info(f"ℹ️ No override config for port {port_number}, skipping.")
                continue

            override = override_ports[port_number]
            payload = {}

            if "name"               in override: payload["name"]               = override["name"]
            if "enabled"            in override: payload["enabled"]            = override["enabled"]
            if "type"               in override: payload["type"]               = override["type"]
            if "vlan"               in override: payload["vlan"]               = override["vlan"]
            if "allowedVlans"       in override and override.get("type") == "trunk":
                payload["allowedVlans"] = override["allowedVlans"]
            if "dropUntaggedTraffic" in override:
                payload["dropUntaggedTraffic"] = override["dropUntaggedTraffic"]
            if "poeEnabled"         in override: payload["poeEnabled"]         = override["poeEnabled"]
            if "accessPolicy"       in override: payload["accessPolicy"]       = override["accessPolicy"]

            if payload.get("type") == "wan":
                payload = {k: payload[k] for k in ("name", "enabled") if k in payload}

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