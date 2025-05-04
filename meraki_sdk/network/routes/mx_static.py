# meraki_sdk/network/routes/mx_static.py

import logging
from meraki.exceptions import APIError

logger = logging.getLogger(__name__)

def configure_static_routes(dashboard, network_id, static_routes, resolved_vlans):
    """
    Configure static routes on a Meraki network using resolved VLAN gateway IPs.

    Args:
        dashboard: Authenticated Meraki Dashboard API session.
        network_id: Meraki network ID.
        static_routes: List of static route dicts.
        resolved_vlans: List of VLANs (from resolved config) including gateway IPs.
    """
    logger.info(f"🛣️ Starting static route configuration for network {network_id}...")

    if not static_routes:
        logger.info("ℹ️ No static routes defined. Skipping.")
        return

    for route in static_routes:
        # Handle dynamic gateway resolution
        gw_ref = route.get("gatewayRef")  # e.g. "mgmt", "guest", or VLAN ID
        gateway_ip = route.get("gatewayIp")

        if gw_ref and not gateway_ip:
            matched = next((v for v in resolved_vlans if v.get("id") == gw_ref or v.get("name") == gw_ref), None)
            if matched:
                gateway_ip = matched["gatewayIp"]
            else:
                logger.warning(f"⚠️ Could not resolve gatewayRef '{gw_ref}' — skipping route '{route['name']}'")
                continue

        try:
            logger.info(f"➕ Creating static route: {route['name']} → {gateway_ip}")
            dashboard.appliance.createNetworkApplianceStaticRoute(
                networkId     = network_id,
                name          = route["name"],
                subnet        = route["subnet"],
                gatewayIp     = gateway_ip,
                active        = route.get("active", True),
                defaultGateway= route.get("defaultGateway", False),
                ipVersion     = route.get("ipVersion")
            )
            logger.info(f"✅ Static route '{route['name']}' created.")
        except APIError as e:
            logger.error(f"❌ Failed to create static route '{route.get('name', 'Unnamed')}': {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error while creating static route: {e}")

    logger.info(f"🏁 Static route configuration complete for network {network_id}.")