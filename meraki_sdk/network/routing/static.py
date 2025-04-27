# meraki_sdk/network/routing/static.py

import logging
from meraki.exceptions import APIError

logger = logging.getLogger(__name__)

def configure_static_routes(dashboard, network_id, static_routes):
    """
    Configure static routes on a Meraki network.

    Args:
        dashboard: Authenticated Meraki Dashboard API session.
        network_id: The network ID.
        static_routes: A list of static route dictionaries.
    """
    logger.info(f"🛣️ Starting static route configuration for network {network_id}...")

    if not static_routes:
        logger.info("ℹ️ No static routes defined. Skipping.")
        return

    for route in static_routes:
        try:
            logger.info(f"➕ Creating static route: {route['name']}")
            dashboard.appliance.createNetworkApplianceStaticRoute(
                networkId     = network_id,
                name          = route["name"],
                subnet        = route["subnet"],
                gatewayIp     = route["gatewayIp"],
                active        = route.get("active", True),
                defaultGateway= route.get("defaultGateway", False),
                ipVersion     = route.get("ipVersion")   # only set if present
            )
            logger.info(f"✅ Static route '{route['name']}' created.")
        except APIError as e:
            logger.error(f"❌ Failed to create static route '{route.get('name', 'Unnamed')}': {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error while creating static route: {e}")

    logger.info(f"🏁 Static route configuration complete for network {network_id}.")