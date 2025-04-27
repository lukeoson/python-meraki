# meraki_sdk/network/mx.py

import logging
import json
import ipaddress
from meraki.exceptions import APIError
from meraki_sdk.network.vlans.exclusions import load_exclusion_overrides, get_vlan_exclusion
from meraki_sdk.network.vlans.fixed_assignments import load_fixed_assignments, get_vlan_fixed_assignments

logger = logging.getLogger(__name__)

def ensure_vlans_enabled(dashboard, network_id):
    try:
        current = dashboard.appliance.getNetworkApplianceVlansSettings(
            networkId=network_id
        )
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

def merge_fixed_assignments(vlan, fixed_assignments_data):
    if "fixedIpAssignments" not in vlan:
        vlan["fixedIpAssignments"] = {}

    yaml_assignments = get_vlan_fixed_assignments(vlan, fixed_assignments_data)

    # First pass: merge without overwriting existing MACs
    for mac, details in yaml_assignments.items():
        if mac in vlan["fixedIpAssignments"]:
            logger.warning(f"⚠️ Conflict on MAC {mac} in VLAN {vlan.get('name', 'Unnamed')}: keeping config.json assignment, ignoring YAML.")
            continue
        vlan["fixedIpAssignments"][mac] = details

    # Second pass: check for duplicate IPs
    seen_ips = {}
    for mac, details in list(vlan["fixedIpAssignments"].items()):
        ip = details.get("ip")
        if not ip:
            continue
        if ip in seen_ips:
            # IP conflict! Keep earlier MAC (JSON wins because it’s first)
            logger.error(f"❌ Duplicate IP {ip} assigned in VLAN {vlan.get('name', 'Unnamed')}. Keeping {seen_ips[ip]}, removing {mac}.")
            del vlan["fixedIpAssignments"][mac]
        else:
            seen_ips[ip] = mac

    # Optional: log final mapping
    logger.info(f"🗺️ Final fixed IP assignments for VLAN {vlan.get('name', 'Unnamed')}:")
    for mac, details in vlan["fixedIpAssignments"].items():
        logger.info(f"   📌 {mac} → {details['ip']} ({details.get('name', 'Unnamed Device')})")

def generate_auto_fixed_assignments_from_reserved(devices, vlan):
    """
    Auto-generate fixed IP assignments for devices using the VLAN's reserved IP ranges,
    prioritizing based on device role (north → south).
    """
    auto_assignments = {}

    if not vlan or "subnet" not in vlan or "reservedIpRanges" not in vlan:
        logger.error("❌ VLAN missing 'subnet' or 'reservedIpRanges'. Cannot auto-assign.")
        return {}

    try:
        subnet = ipaddress.IPv4Network(vlan["subnet"])
    except ValueError as e:
        logger.error(f"❌ Invalid subnet '{vlan['subnet']}': {e}")
        return {}

    reserved_ips = []
    for r in vlan["reservedIpRanges"]:
        start = ipaddress.IPv4Address(r["start"])
        end = ipaddress.IPv4Address(r["end"])
        current = start
        while current <= end:
            reserved_ips.append(str(current))
            current += 1

    reserved_ips = sorted(reserved_ips, key=lambda ip: ipaddress.IPv4Address(ip))

    if not reserved_ips:
        logger.warning("⚠️ No reserved IPs found to auto-assign.")
        return {}

    if len(reserved_ips) < len(devices):
        logger.warning(f"⚠️ Only {len(reserved_ips)} reserved IPs available for {len(devices)} devices.")

    # 🌐 Device role priority map
    DEVICE_PRIORITY = {
        "MX": 1,
        "MG": 2,
        "MS": 3,
        "MR": 4,
        "MV": 5,
        "MT": 6,
    }

    def device_sort_key(device):
        model = device.get("model", "")
        prefix = model[:2]  # e.g., MX, MG, etc.
        return DEVICE_PRIORITY.get(prefix, 999), device.get("serial", "")

    sorted_devices = sorted(devices, key=device_sort_key)

    # 🛡️ Assignment Plan Preview
    logger.info("📋 Planned Fixed IP Assignments (priority order):")
    for device, ip in zip(sorted_devices, reserved_ips):
        name = device.get("name") or device.get("mac")
        model = device.get("model", "Unknown")
        logger.info(f"   🔗 {model} | {name} → {ip}")

    for device, ip in zip(sorted_devices, reserved_ips):
        mac = device.get("mac")
        name = device.get("name") or mac

        if not mac:
            logger.warning(f"⚠️ Skipping device without MAC: {device}")
            continue

        auto_assignments[mac] = {
            "ip": ip,
            "name": name,
            "tags": ["MGMT", "auto-fixed"],
            "comment": f"Auto-assigned ({name})"
        }
        logger.debug(f"🔗 {mac} → {ip} ({name})")

    return auto_assignments

def configure_mx_vlans(dashboard, network_id, config):
    try:
        logger.info("🧑‍🔬 Starting MX VLAN configuration...")
        ensure_vlans_enabled(dashboard, network_id)

        # 🚀 Load overrides and fixed assignments
        exclusion_overrides = load_exclusion_overrides()
        fixed_assignments_data = load_fixed_assignments()

        for vlan in config["vlans"]:
            vlan_id = str(vlan["id"])
            name = vlan["name"]
            subnet = vlan["subnet"]
            gateway = vlan["gatewayIp"]

            # 🔗 Merge manual fixed assignments
            merge_fixed_assignments(vlan, fixed_assignments_data)

            # 🔥 Reserved IPs must be created BEFORE assigning fixed IPs
            if not vlan.get("reservedIpRanges"):
                logger.info(f"🔧 Auto-generating reserved IPs for VLAN {name}")
                vlan["reservedIpRanges"] = get_vlan_exclusion(vlan, default_ratio=0.25, per_vlan_overrides=exclusion_overrides)
            else:
                logger.info(f"📜 Using manually defined reserved IPs for VLAN {name}")

            # 🚀 Auto-assign infra devices IF this is the management VLAN
            management_vlan_name = config["base"].get("management_vlan", {}).get("name", "").lower()
            if vlan.get("name", "").lower() == management_vlan_name:
                logger.info(f"🧠 Auto-assigning fixed IPs to network infrastructure devices on {vlan['name']}...")
                try:
                    all_devices = dashboard.networks.getNetworkDevices(network_id)
                    infra_devices = [d for d in all_devices if any(m in d.get("model", "") for m in ["MX", "MV", "MG"])]
                    auto_assignments = generate_auto_fixed_assignments_from_reserved(infra_devices, vlan)

                    for mac, details in auto_assignments.items():
                        vlan["fixedIpAssignments"][mac] = details  # Always overwrite

                    logger.info(f"✅ Auto-assigned {len(auto_assignments)} Meraki infrastructure devices.")
                except Exception as e:
                    logger.error(f"❌ Failed to auto-generate infra assignments: {e}")

            # 🏗️ Step 1: Create minimal VLAN
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
                    continue  # Skip to next VLAN

            # 🏗️ Step 2: Update VLAN with full config
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