import logging
from meraki.exceptions import APIError

logger = logging.getLogger(__name__)

def configure_outbound_rules(dashboard, network_id, rules):
    try:
        logger.info(f"🚪 Configuring Outbound Firewall Rules for network {network_id}...")

        normalized_rules = []
        for rule in rules:
            normalized_rule = {
                "comment": rule.get("comment", ""),
                "policy": rule["policy"],
                "protocol": rule.get("protocol", "any"),
                "srcCidr": rule["srcCidr"],  # must be exact casing
                "srcPort": rule.get("srcPort", "any"),
                "destCidr": rule["destCidr"],  # must be exact casing
                "destPort": rule.get("destPort", "any"),
                "syslogEnabled": rule.get("syslogEnabled", False),
            }
            normalized_rules.append(normalized_rule)

        dashboard.appliance.updateNetworkApplianceFirewallL3FirewallRules(
            networkId=network_id,
            rules=normalized_rules
        )
        logger.info("✅ Outbound firewall rules configured successfully.")
    except APIError as e:
        logger.error(f"❌ API Error while configuring outbound firewall rules: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while configuring outbound firewall rules: {e}")

def configure_inbound_rules(dashboard, network_id, rules):
    """
    Configure inbound (ingress) firewall rules.
    """
    try:
        logger.info(f"🚪 Configuring Inbound Firewall Rules for network {network_id}...")
        
        # Normalize field names for inbound rules
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
                "syslogEnabled": rule.get("syslogEnabled", False)
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