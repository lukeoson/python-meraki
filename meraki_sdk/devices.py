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

