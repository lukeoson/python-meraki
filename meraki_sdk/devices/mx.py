# meraki_sdk/devices/mx.py
import logging
from meraki.exceptions import APIError

logger = logging.getLogger(__name__)

# meraki_sdk/devices/mx.py
import logging
from meraki.exceptions import APIError

logger = logging.getLogger(__name__)

def ensure_vlans_enabled(dashboard, network_id):
    """
    Checks if VLANs are enabled on the MX network. If not, enables them.
    """
    try:
        current = dashboard.appliance.getNetworkApplianceVlansSettings(
            networkId=network_id
        )
        if current.get("vlansEnabled"):
            logger.info(f"✅ VLANs already enabled for network {network_id}. No action taken.")
            return current
        else:
            logger.info(f"🔧 Enabling VLANs for network {network_id}...")
            response = dashboard.appliance.updateNetworkApplianceVlansSettings(
                networkId=network_id,
                vlansEnabled=True
            )
            logger.info(f"✅ VLANs successfully enabled for network {network_id}.")
            return response
    except APIError as e:
        logger.error(f"❌ APIError while managing VLANs for network {network_id}: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while managing VLANs: {e}")

def configure_mx_vlan(dashboard, network_id, config):
    """
    Configure VLAN for the MX appliance based on the config.
    """
    try:
        # Get VLAN configuration from the config file
        vlan_config = config.get("vlan", {})
        
        # Extract VLAN parameters from the config
        vlan_id = vlan_config.get("id")
        vlan_name = vlan_config.get("name")
        subnet = vlan_config.get("subnet")
        gateway_ip = vlan_config.get("gatewayIp")

        # Check that necessary parameters are present
        if not vlan_id or not vlan_name or not subnet or not gateway_ip:
            raise ValueError("Missing required VLAN configuration values in config.json")

        # Create VLAN in the network using the API
        response = dashboard.appliance.createNetworkApplianceVlan(
            network_id,
            vlan_id,
            vlan_name,
            subnet=subnet,
            applianceIp=gateway_ip
        )
        
        logger.info(f"✅ Created VLAN {vlan_id} ({vlan_name}) with subnet {subnet} and gateway {gateway_ip}.")
        return response
    except APIError as e:
        logger.error(f"❌ Failed to configure VLAN: {e}")
    except ValueError as e:
        logger.error(f"❌ {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while configuring VLAN: {e}")

def apply_mx_configurations(dashboard, network_id, config):
    """
    Apply VLAN configuration for the MX appliance.
    """
    try:
        logger.info("Starting MX appliance configuration...")
        # First, ensure VLANs are enabled before proceeding with VLAN configuration
        ensure_vlans_enabled(dashboard, network_id)
        
        # Apply VLAN configuration from the config
        configure_mx_vlan(dashboard, network_id, config)
        logger.info(f"✅ MX appliance VLAN configuration applied successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to apply MX configurations: {e}")