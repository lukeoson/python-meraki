# meraki_sdk/network_constructs/vlans/mx.py
import logging
import json
from meraki.exceptions import APIError
from meraki_sdk.network_constructs.vlans.exclusions import load_exclusion_overrides, get_vlan_exclusion
from meraki_sdk.network_constructs.vlans.fixed_assignments import (
    auto_generate_fixed_assignments_for_vlan_10,
    load_fixed_assignments,
    get_vlan_fixed_assignments,
)

logger = logging.getLogger(__name__)


def ensure_vlans_enabled(dashboard, network_id):
    try:
        current = dashboard.appliance.getNetworkApplianceVlansSettings(networkId=network_id)
        if current.get("vlansEnabled"):
            logger.info(f"✅ VLANs already enabled for network {network_id}.")
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


def configure_mx_vlans(dashboard, network_id, config):
    try:
        logger.info("🧑‍🔬 Starting MX VLAN configuration...")
        ensure_vlans_enabled(dashboard, network_id)

        # 🚀 Inject DHCP reserved ranges and Fixed IPs here
        exclusion_overrides = load_exclusion_overrides()
        fixed_assignments_data = load_fixed_assignments()

        for vlan in config["vlans"]:
            vlan_id = str(vlan["id"])
            name = vlan["name"]
            subnet = vlan["subnet"]
            gateway = vlan["gatewayIp"]

            # 🔥 Reserved IPs
            if not vlan.get("reservedIpRanges"):
                logger.info(f"🔧 Auto-generating reserved IPs for VLAN {name}")
                vlan["reservedIpRanges"] = get_vlan_exclusion(
                    vlan,
                    default_ratio=0.25,
                    per_vlan_overrides=exclusion_overrides
                )
            else:
                logger.info(f"📜 Using manually defined reserved IPs for VLAN {name}")

            # 🎯 Fixed IPs for VLAN 10
            if vlan_id == "10":
                logger.info(f"🔧 Auto-assigning Meraki devices fixed IPs in VLAN {name}")
                auto_generate_fixed_assignments_for_vlan_10(dashboard, network_id, vlan)

                # 📝 Merge YAML manual overrides *on top* of auto-generated
                manual_assignments = get_vlan_fixed_assignments(vlan, fixed_assignments_data)
                if manual_assignments:
                    vlan.setdefault("fixedIpAssignments", {}).update(manual_assignments)
                    logger.info(f"📝 Merged manual fixed IP assignments for VLAN {name}")

            # Step 1: Create minimal VLAN
            create_payload = {
                "id": vlan_id,
                "name": name,
                "subnet": subnet,
                "applianceIp": gateway
            }
            try:
                dashboard.appliance.createNetworkApplianceVlan(
                    networkId=network_id,
                    **create_payload
                )
                logger.info(f"✅ Created base VLAN {vlan_id} ({name})")
            except APIError as e:
                if "already exists" in str(e):
                    logger.warning(f"⚠️ VLAN {vlan_id} already exists. Proceeding to update.")
                else:
                    logger.error(f"❌ Failed to create VLAN {vlan_id}: {e}")
                    continue  # skip to next VLAN

            # Step 2: Update with advanced DHCP settings
            update_payload = {
                "name": name,
                "subnet": subnet,
                "applianceIp": gateway,
                "dhcpHandling": vlan.get("dhcpHandling", "Run a DHCP server"),
                "dnsNameservers": vlan.get("dnsNameservers", "upstream_dns"),
                "dhcpLeaseTime": vlan.get("dhcpLeaseTime", "12 hours"),
                "reservedIpRanges": vlan.get("reservedIpRanges", []),
                "fixedIpAssignments": vlan.get("fixedIpAssignments", {})
            }

            logger.debug(f"🔍 VLAN {vlan_id} update payload:\n{json.dumps(update_payload, indent=2)}")

            try:
                dashboard.appliance.updateNetworkApplianceVlan(
                    networkId=network_id,
                    vlanId=vlan_id,
                    **update_payload
                )
                logger.info(f"✅ Updated VLAN {vlan_id} with full config.")
            except APIError as e:
                logger.error(f"❌ Failed to update VLAN {vlan_id}: {e}")
            except Exception as e:
                logger.error(f"❌ Unexpected error while updating VLAN {vlan_id}: {e}")

        logger.info("✅ MX VLAN configuration applied successfully.")

    except Exception as e:
        logger.error(f"❌ Failed to apply MX VLAN configurations: {e}")
