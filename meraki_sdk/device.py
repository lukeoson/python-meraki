import logging
import requests
import os

from meraki.exceptions import APIError

logger = logging.getLogger(__name__)

def claim_devices(dashboard, network_id, serials):
    logger.info(f"Claiming devices to network {network_id}")
    try:
        dashboard.networks.claimNetworkDevices(network_id, serials=serials)
        logger.info("✅ Devices claimed successfully.")
    except APIError as e:
        logger.error(f"❌ Failed to claim devices: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error while claiming devices: {e}")

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
    type_counters = {}
    named_devices = []

    for device in devices:
        device_type = device["type"].upper()  # Ensure the type is uppercase
        type_counters[device_type] = type_counters.get(device_type, 0) + 1
        seq = f"{type_counters[device_type]:02d}"  # Generate a sequence number with two digits

        name_parts = [
            naming_config["city"],
            naming_config["building"],
            naming_config["room"],
            naming_config["function"],
            device_type,  # Device type (MX, MG, etc.)
            seq  # Sequence number
        ]

        device_name = "-".join(name_parts).upper()  # Convert the full name to uppercase
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

