# meraki_sdk/devices/__init__.py

import logging
from .mx_vlans import apply_mx_vlans
from .mx_ports import configure_mx_ports
from ..device import (
    set_device_address,
    set_device_names,
    generate_device_names,
)

def setup_devices(
    dashboard,
    network_id,
    config,
    *,
    configure_addresses=True,
    configure_names=True,
    configure_vlans=True,
    configure_ports=True
):
    """
    Full post-claim setup: addresses, names, VLANs, ports.
    """
    logger = logging.getLogger(__name__)
    logger.info("⚙️ Starting post-claim device configuration...")

    if configure_addresses:
        logger.info("📫 Setting device addresses...")
        set_device_address(dashboard, [d["serial"] for d in config["devices"]["devices"]])

    if configure_names:
        logger.info("🏷️ Setting device names...")
        named_devices = generate_device_names(
            config["devices"]["devices"],
            config["base"]["naming"]
        )
        set_device_names(dashboard, network_id, named_devices)

    if configure_vlans:
        logger.info("🌐 Configuring MX VLANs...")
        apply_mx_vlans(dashboard, network_id, config)

    if configure_ports:
        logger.info("🔌 Configuring MX ports...")
        configure_mx_ports(dashboard, network_id, config)

    logger.info("✅ Post-claim device configuration completed successfully.")