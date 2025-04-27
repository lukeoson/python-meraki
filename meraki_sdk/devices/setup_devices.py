# meraki_sdk/devices/setup_devices.py

import logging
from meraki_sdk.device import (
    claim_devices,
    set_device_address,
    set_device_names,
    generate_device_names,
)

logger = logging.getLogger(__name__)

def setup_devices(dashboard, network_id, config):
    """
    Full post-claim setup: claim devices, set address, set names.
    (Port configuration is now handled in setup_network_constructs.)
    """
    logger.info("📦 Starting post-claim device configuration...")

    # 1. Claim devices
    serials = [d["serial"] for d in config["devices"]["devices"]]
    claim_devices(dashboard, network_id, serials)

    # 2. Set device addresses
    set_device_address(dashboard, serials)

    # 3. Set device names
    named_devices = generate_device_names(
        config["devices"]["devices"],
        config["base"]["naming"]
    )
    set_device_names(dashboard, network_id, named_devices)

    logger.info("✅ Post-claim device configuration completed successfully.")
    return named_devices