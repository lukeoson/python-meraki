# meraki_sdk/network/wireless/mx_wireless.py

import logging
import json
from meraki.exceptions import APIError

logger = logging.getLogger(__name__)

def apply_mx_wireless(dashboard, network_id, config):
    """
    Apply MX wireless SSID settings using `config`, expected to contain:
    - `defaults`: base config applied to all SSIDs
    - `ssids`: list of individual SSID configs
    """

    defaults = config.get("defaults", {})
    ssids = config.get("ssids", [])

    # Check for wireless-capable MX devices before proceeding
    try:
        devices = dashboard.networks.getNetworkDevices(network_id)
        wireless_capable = any("MX68CW" in d.get("model", "") for d in devices)
        if not wireless_capable:
            models = [d.get("model", "Unknown") for d in devices if "MX" in d.get("model", "")]
            logger.warning(f"⚠️ No wireless-capable MX device found in network {network_id}. Skipping wireless config as the following devices are not wireless capable: {', '.join(models)}.")
            return
    except Exception as e:
        logger.error(f"❌ Failed to retrieve devices for wireless capability check: {e}")
        return

    if not ssids:
        logger.warning(f"⚠️ No SSIDs defined in config for network {network_id}. Skipping.")
        return

    for i, ssid in enumerate(ssids):
        ssid_number = ssid.get("number", i)

        # Merge defaults with override
        final = defaults.copy()
        final.update(ssid)

        payload = {k: v for k, v in final.items() if k != "number"}
        name = payload.get("name", f"SSID {ssid_number}")

        try:
            logger.info(f"📶 Configuring SSID '{name}' on slot {ssid_number} (network: {network_id})")
            logger.debug(f"🧾 Payload:\n{json.dumps(payload, indent=2)}")

            response = dashboard.appliance.updateNetworkApplianceSsid(
                networkId=network_id,
                number=ssid_number,
                **payload
            )

            logger.debug(f"✅ API Response for '{name}': {response}")

        except APIError as e:
            logger.error(f"❌ APIError on SSID '{name}' (slot {ssid_number}): {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error on SSID '{name}' (slot {ssid_number}): {e}")

    logger.info("✅ All SSIDs applied successfully.")