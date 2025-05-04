# network/firewall/mx_firewall.py
#
# 🔥 Handles MX firewall rule configuration: outbound + inbound
# Supports VLAN(x) macro substitution (e.g. VLAN(10).* → actual subnet)

import logging
import re
from meraki.exceptions import APIError

logger = logging.getLogger(__name__)

def _resolve_vlan_macros(rules, resolved_vlans):
    """
    Replace VLAN(x).* or VLAN(x).y with actual subnet/IP from resolved_vlans.
    """
    def replace_macro(cidr):
        if not isinstance(cidr, str):
            return cidr

        match = re.match(r"VLAN\((\d+)\)\.(\*|\d+)", cidr)
        if not match:
            return cidr

        vlan_id = int(match.group(1))
        host_part = match.group(2)

        vlan = next((v for v in resolved_vlans if int(v.get("id")) == vlan_id), None)
        if not vlan:
            logger.warning(f"⚠️ No resolved VLAN found with ID {vlan_id} for macro '{cidr}'")
            return cidr

        base_subnet = vlan.get("subnet")
        if not base_subnet:
            logger.warning(f"⚠️ VLAN {vlan_id} has no subnet defined for macro '{cidr}'")
            return cidr

        net = base_subnet.rsplit(".", 1)[0]
        resolved = f"{net}.{host_part}/32" if host_part != "*" else base_subnet
        logger.debug(f"[DEBUG] Resolved macro '{cidr}' → '{resolved}'")
        return resolved

    # 🔄 Apply replacement to all relevant rules
    for rule in rules:
        rule["srcCidr"] = replace_macro(rule.get("srcCidr", ""))
        rule["destCidr"] = replace_macro(rule.get("destCidr", ""))
    
    return rules

def configure_outbound_rules(dashboard, network_id, rules, resolved_vlans):
    try:
        logger.info(f"🚪 Configuring Outbound Firewall Rules for network {network_id}...")

        rules = _resolve_vlan_macros(rules, resolved_vlans)

        normalized_rules = []
        for rule in rules:
            normalized_rules.append({
                "comment": rule.get("comment", ""),
                "policy": rule["policy"],
                "protocol": rule.get("protocol", "any"),
                "srcCidr": rule["srcCidr"],
                "srcPort": rule.get("srcPort", "any"),
                "destCidr": rule["destCidr"],
                "destPort": rule.get("destPort", "any"),
                "syslogEnabled": rule.get("syslogEnabled", False),
            })

        dashboard.appliance.updateNetworkApplianceFirewallL3FirewallRules(
            networkId=network_id,
            rules=normalized_rules
        )
        logger.info("✅ Outbound firewall rules configured successfully.")
    except APIError as e:
        logger.error(f"❌ API Error while configuring outbound firewall rules: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while configuring outbound firewall rules: {e}")

def configure_inbound_rules(dashboard, network_id, rules, resolved_vlans):
    try:
        logger.info(f"🚪 Configuring Inbound Firewall Rules for network {network_id}...")

        rules = _resolve_vlan_macros(rules, resolved_vlans)

        normalized_rules = []
        for rule in rules:
            normalized_rules.append({
                "policy": rule["policy"],
                "protocol": rule["protocol"],
                "srcCidr": rule["srcCidr"],
                "srcPort": rule.get("srcPort", "any"),
                "destCidr": rule["destCidr"],
                "destPort": rule.get("destPort", "any"),
                "comment": rule.get("comment", ""),
                "syslogEnabled": rule.get("syslogEnabled", False),
            })

        dashboard.appliance.updateNetworkApplianceFirewallInboundFirewallRules(
            networkId=network_id,
            rules=normalized_rules
        )
        logger.info("✅ Inbound firewall rules configured successfully.")
    except APIError as e:
        logger.error(f"❌ API Error while configuring inbound firewall rules: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while configuring inbound firewall rules: {e}")