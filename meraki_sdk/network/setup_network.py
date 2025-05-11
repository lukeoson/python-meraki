# meraki_sdk/network/setup_network.py

import logging

from meraki_sdk.network.vlans.mx import configure_mx_vlans
from meraki_sdk.network.routes.mx_static import configure_static_routes
from meraki_sdk.network.ports.mx_ports import configure_mx_ports
from meraki_sdk.network.firewall.mx_firewall import configure_outbound_rules, configure_inbound_rules
from meraki_sdk.network.wireless.mx_wireless import apply_mx_wireless
from meraki_sdk.network.vpn.mx_autovpn import configure_mx_autovpn

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
    if do_static_routes and config.get("mx_static_routes"):
        logger.info("🛣️ Configuring Static Routes...")
        configure_static_routes(dashboard, network_id, config["mx_static_routes"], config["vlans"])
    else:
        logger.info("⚠️ No static routes defined, skipping.")

    # 4. Firewall Rules
    firewall_config = config.get("firewall", {})
    
    logger.debug(f"[DEBUG] Outbound Firewall Rules: {firewall_config.get('outbound_rules', [])}")
    logger.debug(f"[DEBUG] Inbound Firewall Rules: {firewall_config.get('inbound_rules', [])}")
    
    outbound_rules = firewall_config.get("outbound_rules", [])
    if outbound_rules:
        logger.info("🚪 Configuring Outbound Firewall Rules...")
        configure_outbound_rules(dashboard, network_id, outbound_rules, config["vlans"])
    else:
        logger.info("⚠️ No outbound firewall rules found, skipping.")
    
    inbound_rules = firewall_config.get("inbound_rules", [])
    if inbound_rules:
        logger.info("🚪 Configuring Inbound Firewall Rules...")
        configure_inbound_rules(dashboard, network_id, inbound_rules, config["vlans"])
    else:
        logger.info("⚠️ No inbound firewall rules found, skipping.")
    
    # 5. AutoVPN Configuration
    if do_vpn and config.get("mx_autovpn"):
        logger.info("🔒 Configuring AutoVPN...")
        configure_mx_autovpn(dashboard, network_id, config["mx_autovpn"])
    else:
        logger.info("⚠️ No AutoVPN configuration found or VPN flag not enabled.")
    
    # 6. MX Wireless (config["mx_wireless"])
    if do_wireless:
        wireless_config = config.get("mx_wireless", {})
        if wireless_config.get("ssids"):
            logger.info("📶 Configuring MX wireless SSIDs...")
            apply_mx_wireless(dashboard, network_id, wireless_config)
        else:
            logger.info("⚠️ No SSID configuration found under 'mx_wireless', skipping.")
    else:
        logger.info("⚠️ Wireless configuration skipped (flag disabled).")


    if do_ospf:
        logger.info("📡 OSPF configuration not yet implemented.")
    if do_bgp:
        logger.info("🌍 BGP configuration not yet implemented.")