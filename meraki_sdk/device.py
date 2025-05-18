import logging
import requests
import os

from meraki.exceptions import APIError

logger = logging.getLogger(__name__)

def claim_devices(dashboard, network_id, serials):
    logger.info(f"🔍 Starting device claim to network {network_id}")
    logger.debug(f"Serials to claim: {serials}")
    for serial in serials:
        try:
            dashboard.networks.claimNetworkDevices(network_id, serials=[serial])
            logger.info(f"✅ Claimed device {serial}")
        except APIError as e:
            if "already claimed" in str(e).lower():
                logger.warning(f"⚠️ Device {serial} already claimed. Skipping.")
            else:
                logger.error(f"❌ Failed to claim {serial}: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error for {serial}: {e}")

def remove_devices_from_network(dashboard, network_id, devices):
    logger.info(f"🧹 Attempting to remove devices from network: {network_id}")
    for device in devices:
        serial = device["serial"]
        try:
            dev_info = dashboard.devices.getDevice(serial)
            if dev_info.get("networkId") != network_id:
                logger.info(f"✅ {serial} already not in the target network.")
                continue

            dashboard.networks.removeNetworkDevices(network_id, serial)
            logger.info(f"✅ Removed {serial} from network.")
        except APIError as e:
            if "Device does not belong to a network" in str(e):
                logger.info(f"✅ {serial} already removed from a network.")
            else:
                logger.error(f"❌ Failed to remove {serial}: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error removing {serial}: {e}")

def set_device_address(dashboard, serials, address="18 Percy Street, London, W1T 1DX"):
    logger.info(f"📍 Setting address for all devices to: {address}")
    for serial in serials:
        try:
            dashboard.devices.updateDevice(
                serial=serial,
                address=address,
                moveMapMarker=True
            )
            logger.info(f"✅ Set address for {serial}")
        except Exception as e:
            logger.error(f"❌ Failed to set address for {serial}: {e}")

def generate_device_names(devices, naming_config):
    """
    Generate structured names for Meraki devices using a naming convention.
    Names are of the format CITY-BUILDING-ROOM-FUNCTION-TYPE-SEQ.
    Sequence is per device type (e.g., MX-01, MX-02).
    """

    def matches_rule(device, rule):
        match = rule.get("match", {})
        if "type" in match and match["type"].upper() != device["type"].upper():
            return False
        if "tags" in match:
            device_tags = set(device.get("tags", []))
            required_tags = set(match["tags"])
            if not required_tags.issubset(device_tags):
                return False
        return True

    rules = naming_config.get("rules", [])
    defaults = naming_config.get("defaults", {})

    type_counters = {}
    named_devices = []

    for device in devices:
        device_type = device["type"].upper()
        type_counters[device_type] = type_counters.get(device_type, 0) + 1
        seq = f"{type_counters[device_type]:02d}"

        matched_rule = next((r for r in rules if matches_rule(device, r)), {})

        def resolve_key(key):
            return (
                matched_rule.get(key) or
                device.get("location", {}).get(key) or
                defaults.get(key) or
                naming_config.get(key)
            )

        city = resolve_key("city")
        building = resolve_key("building")
        room = resolve_key("room")
        function = resolve_key("function")

        if not all([city, building, room, function]):
            raise ValueError(f"❌ Missing naming value for device {device['serial']} — resolved as: "
                             f"city={city}, building={building}, room={room}, function={function}")

        name_parts = [city, building, room, function, device_type, seq]
        device_name = "-".join(name_parts).upper()
        named_devices.append({"serial": device["serial"], "name": device_name})

    return named_devices


def set_device_names(dashboard, network_id, named_devices):
    """
    Set device names in the Meraki dashboard based on the generated names.
    """
    for device in named_devices:
        dashboard.devices.updateDevice(
            device["serial"],
            name=device["name"]
        )
