import logging

logger = logging.getLogger(__name__)

def configure_mx_autovpn(dashboard, network_id, config):
    """
    Applies MX AutoVPN configuration using the Meraki Dashboard API.

    Args:
        dashboard: Authenticated Meraki SDK client
        network_id: The target network's Meraki ID
        config: The resolved mx_autovpn config dict for this network
    """

    if not config or "mode" not in config:
        logger.info(f"🔕 Skipping AutoVPN config for {network_id}: no config or mode specified.")
        return

    logger.info(f"🔐 Applying AutoVPN config to network {network_id} with mode: {config['mode']}")

    try:
        dashboard.appliance.updateNetworkApplianceVpnSiteToSiteVpn(
            networkId=network_id,
            **config
        )
        logger.info(f"✅ AutoVPN config applied to {network_id}")
    except Exception as e:
        logger.error(f"❌ Failed to apply AutoVPN config to {network_id}: {e}")