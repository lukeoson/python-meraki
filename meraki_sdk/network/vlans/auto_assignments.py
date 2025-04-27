def generate_auto_fixed_assignments_from_reserved(devices, vlan):
    """
    Auto-generate fixed IP assignments from reserved IP range for the VLAN.
    """
    import ipaddress

    logger = logging.getLogger(__name__)
    auto_assignments = {}

    if not vlan or "subnet" not in vlan or "reservedIpRanges" not in vlan:
        logger.error("❌ VLAN missing 'subnet' or 'reservedIpRanges' fields.")
        return {}

    try:
        subnet = ipaddress.IPv4Network(vlan["subnet"])
    except ValueError as e:
        logger.error(f"❌ Invalid subnet '{vlan['subnet']}': {e}")
        return {}

    # Collect all available reserved IPs
    reserved_ips = []
    for r in vlan["reservedIpRanges"]:
        start = ipaddress.IPv4Address(r["start"])
        end = ipaddress.IPv4Address(r["end"])
        reserved_ips.extend([str(ip) for ip in ipaddress.summarize_address_range(start, end)][0].hosts())

    reserved_ips = sorted(reserved_ips)

    if len(reserved_ips) < len(devices):
        logger.warning("⚠️ Not enough reserved IPs for all devices. Some devices will not be assigned.")

    for device, ip_obj in zip(devices, reserved_ips):
        mac = device.get("mac")
        name = device.get("name") or mac
        model = device.get("model", "Unknown Model")

        if not mac:
            logger.warning(f"⚠️ Device with no MAC skipped: {device}")
            continue

        auto_assignments[mac] = {
            "ip": str(ip_obj),
            "name": name,
            "tags": ["MGMT", "auto-fixed"],
            "comment": f"Auto-assigned ({name})"
        }
        logger.debug(f"🔗 Auto-assigned {mac} → {ip_obj} ({name})")

    logger.info(f"✅ Auto-fixed {len(auto_assignments)} devices using reserved IPs.")
    return auto_assignments