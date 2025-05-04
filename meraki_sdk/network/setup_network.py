# meraki_sdk/network/setup_network.py

import logging

from meraki_sdk.network.vlans.mx import configure_mx_vlans
from meraki_sdk.network.routing.static import configure_static_routes
from meraki_sdk.network.ports.mx_ports import configure_mx_ports
from meraki_sdk.network.firewall import configure_outbound_rules, configure_inbound_rules
from meraki_sdk.network.wireless.mx_wireless import apply_mx_wireless

logger = logging.getLogger(__name__)

def setup_network(
    dashboard,
    network_id,
    config,
    *,
    do_vlans=True,
    do_ports=True,
    do_static_routes=True,
    do_firewall=True,
    do_wireless=True,
    do_vpn=False,
    do_ospf=False,
    do_bgp=False,
):
    """
    Apply all logical Meraki network configuration:
    - VLANs
    - MX port profiles
    - Static routes
    - Firewall rules
    - (Optional stubs for VPN, OSPF, BGP)
    """

    # 1. VLAN Configuration
    if do_vlans:
        logger.info("🌐 Configuring MX VLANs...")
        configure_mx_vlans(dashboard, network_id, config)

    # 2. Port Profiles (must come after VLANs)
    if do_ports and config.get("mx_ports"):
        logger.info("🔌 Configuring MX ports...")
        configure_mx_ports(dashboard, network_id, config["mx_ports"])

    # 3. Static Routes
    if do_static_routes and config.get("static_routes"):
        logger.info("🛣️ Configuring Static Routes...")
        configure_static_routes(dashboard, network_id, config["static_routes"])
    else:
        logger.info("⚠️ No static routes defined, skipping.")

    # 4. Firewall Rules
    firewall_config = config.get("firewall", {})
    
    outbound_rules = firewall_config.get("outbound_rules", [])
    if outbound_rules:
        logger.info("🚪 Configuring Outbound Firewall Rules...")
        configure_outbound_rules(dashboard, network_id, outbound_rules)
    else:
        logger.info("⚠️ No outbound firewall rules found, skipping.")

    inbound_rules = firewall_config.get("inbound_rules", [])
    if inbound_rules:
        logger.info("🚪 Configuring Inbound Firewall Rules...")
        configure_inbound_rules(dashboard, network_id, inbound_rules)
    else:
        logger.info("⚠️ No inbound firewall rules found, skipping.")
    
    # 5. MX Wireless (config["mx_wireless"])
    if do_wireless:
        wireless_config = config.get("mx_wireless", {})
        if wireless_config.get("ssids"):
            logger.info("📶 Configuring MX wireless SSIDs...")
            apply_mx_wireless(dashboard, network_id, wireless_config)
        else:
            logger.info("⚠️ No SSID configuration found under 'mx_wireless', skipping.")
    else:
        logger.info("⚠️ Wireless configuration skipped (flag disabled).")

    # 6. Not implemented yet
    if do_vpn:
        logger.info("🔐 VPN configuration not yet implemented.")
    if do_ospf:
        logger.info("📡 OSPF configuration not yet implemented.")
    if do_bgp:
        logger.info("🌍 BGP configuration not yet implemented.")