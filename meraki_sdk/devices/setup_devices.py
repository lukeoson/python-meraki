# meraki_sdk/devices/setup_devices.py

import logging
from meraki_sdk.device import (
    claim_devices,
    set_device_address,
    set_device_names,
    generate_device_names,
)

logger = logging.getLogger(__name__)

def setup_devices(dashboard, network_id, inputs):
    """
    Full post-claim setup for Meraki devices:
    - Claim them to the network
    - Set physical address
    - Generate and assign names
    """
    logger.info("📦 Starting post-claim device configuration...")

    # Extract devices and naming config from the inputs
    devices = inputs["devices"]                      # Flat list of device dicts
    naming = inputs["base"].get("naming", {})        # Resolved naming rules (prefix, suffix, etc.)

    # 1. Claim devices to the new network using their serials
    serials = [d["serial"] for d in devices]
    claim_devices(dashboard, network_id, serials)

    # 2. Set location address for all claimed devices
    set_device_address(dashboard, serials)

    # 3. Generate device names (e.g., "LON-PERCY-MX-01") based on the config
    named_devices = generate_device_names(devices, naming)

    # 4. Apply those names to the devices in the dashboard
    set_device_names(dashboard, network_id, named_devices)

    logger.info("✅ Post-claim device configuration completed successfully.")

    # 🧬 Enrich with Meraki API metadata
    try:
        full_device_list = dashboard.networks.getNetworkDevices(network_id)
        serial_to_meta = {d["serial"]: d for d in full_device_list}
        for device in named_devices:
            meta = serial_to_meta.get(device["serial"], {})
            device.update(meta)  # merge model, mac, etc. into device dict
    except Exception as e:
        logger.warning(f"⚠️ Failed to enrich device metadata: {e}")

    return named_devices