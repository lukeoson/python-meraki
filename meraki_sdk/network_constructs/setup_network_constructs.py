# meraki_sdk/network_constructs/setup_network_constructs.py
import logging

from meraki_sdk.network_constructs.vlans.mx       import configure_mx_vlans
from meraki_sdk.network_constructs.routing.static import configure_static_routes
from meraki_sdk.network_constructs.ports.mx_ports import configure_mx_ports

logger = logging.getLogger(__name__)

def setup_network_constructs(
    dashboard,
    network_id,
    config,
    *,
    do_vlans=True,
    do_ports=True,
    do_static_routes=True,
    do_vpn=False,
    do_ospf=False,
    do_bgp=False,
):
    """
    Configure network logical constructs: VLANs, ports, routes, VPN, OSPF, BGP.
    """
    # 1. VLANs
    if do_vlans:
        logger.info("🌐 Configuring MX VLANs...")
        configure_mx_vlans(dashboard, network_id, config)

        # 2. Ports (only after VLANs are on)
        if do_ports and config.get("mx_ports"):
            logger.info("🔌 Configuring MX ports...")
            configure_mx_ports(dashboard, network_id, config["mx_ports"])

    # 3. Static routes
    if do_static_routes and config.get("static_routes"):
        logger.info("🛣️ Configuring Static Routes...")
        configure_static_routes(dashboard, network_id, config["static_routes"])
    else:
        logger.info("⚠️ No static routes defined, skipping.")

    # 4. Future: VPN, OSPF, BGP
    if do_vpn:
        logger.info("🔐 VPN configuration not yet implemented.")
    if do_ospf:
        logger.info("📡 OSPF configuration not yet implemented.")
    if do_bgp:
        logger.info("🌍 BGP configuration not yet implemented.")