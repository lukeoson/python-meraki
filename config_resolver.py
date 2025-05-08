import os
import yaml
import ipaddress
import logging
from copy import deepcopy
from ipam.allocator import IPAMAllocator

CONFIG_DIR = "config"
logger = logging.getLogger(__name__)

# 🔁 Deep merge two nested dicts
def merge_dicts(base, override):
    result = deepcopy(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result

# 🔄 Flatten the grouped device inventory into a flat list of Meraki devices
def flatten_devices(grouped):
    result = []
    for group in grouped.get("groups", []):
        tag = group["tag"]
        for device in group["devices"]:
            d = device.copy()
            if "tags" not in d:
                d["tags"] = [tag]
            result.append(d)
    return result

def resolve_mx_ports(defaults, backend, project_overrides=None):
    config = {"defaults": {}, "ports": []}

    if "mx_ports" in defaults:
        config["ports"] = defaults["mx_ports"]

    try:
        common_config = backend.get_mx_ports()  # ✅ Now uses the backend
        config["defaults"] = common_config.get("defaults", {})
        config["ports"] = common_config.get("ports", config["ports"])
    except Exception as e:
        logger.warning(f"⚠️ Failed to load common mx_ports: {e}")

    if project_overrides:
        override_path = project_overrides.get("mx_ports")
        if isinstance(override_path, str):
            try:
                full_path = os.path.join(CONFIG_DIR, override_path)
                with open(full_path, "r") as f:
                    override = yaml.safe_load(f)
                    config["ports"] = override.get("ports", config["ports"])
                    config["defaults"].update(override.get("defaults", {}))
            except Exception as e:
                logger.warning(f"⚠️ Failed to load project mx_ports override from '{override_path}': {e}")
        elif isinstance(override_path, dict):
            config["ports"] = override_path.get("ports", config["ports"])
            config["defaults"].update(override_path.get("defaults", {}))

    return config

# 📡 Resolve MX static routes config from common + project overrides
def resolve_mx_static_routes(defaults, backend, project_overrides=None, resolved_vlans=None):
    config = {"routes": []}

    if "mx_static_routes" in defaults:
        config["routes"] = defaults["mx_static_routes"]

    try:
        common_routes = backend.get_mx_static_routes()
        config["routes"] = common_routes.get("routes", config["routes"])
    except Exception as e:
        logger.warning(f"⚠️ Failed to load common mx_static_routes: {e}")

    if project_overrides:
        override_path = project_overrides.get("mx_static_routes")
        if isinstance(override_path, str):
            try:
                full_path = os.path.join(CONFIG_DIR, override_path)
                with open(full_path, "r") as f:
                    override = yaml.safe_load(f)
                    config["routes"] = override.get("routes", config["routes"])
            except Exception as e:
                logger.warning(f"⚠️ Failed to load project mx_static_routes override from '{override_path}': {e}")
        elif isinstance(override_path, dict):
            config["routes"] = override_path.get("routes", config["routes"])

    # 🧠 Resolve gatewayRef → gatewayIp using resolved_vlans
    processed = []
    for route in config["routes"]:
        route = deepcopy(route)
        gw_ref = route.get("gatewayRef")

        if gw_ref and not route.get("gatewayIp") and resolved_vlans:
            gw_ref_str = str(gw_ref).lower()
            matched = next(
                (
                    v for v in resolved_vlans
                    if str(v.get("id")) == str(gw_ref) or str(v.get("name", "")).lower() == gw_ref_str
                ),
                None
            )
            if matched:
                route["gatewayIp"] = matched["gatewayIp"]
            else:
                logger.warning(f"⚠️ Could not resolve gatewayRef '{gw_ref}' in route '{route.get('name', 'Unnamed')}'")

        processed.append(route)

    return {"routes": processed}

# 🔥 Resolve MX firewall rules config from common + project overrides
def resolve_firewall_rules(defaults, backend, project_overrides=None, resolved_vlans=None):
    import logging
    from copy import deepcopy
    logger = logging.getLogger(__name__)

    # Base structure with empty rule sets
    config = {
        "outbound_rules": [],
        "inbound_rules": []
    }

    # 1️⃣ Inline fallback from defaults.yaml (rarely used)
    if "firewall" in defaults:
        config.update(defaults["firewall"])

    # 2️⃣ Load shared firewall rules from backend (e.g. common/firewall/mx_firewall.yaml)
    try:
        common_config = backend.get_firewall_rules()
        config.update(common_config)
    except Exception as e:
        logger.warning(f"⚠️ Failed to load common firewall.yaml: {e}")

    # 3️⃣ Project-specific overrides
    if project_overrides:
        override_path = project_overrides.get("firewall")
        if isinstance(override_path, str):
            try:
                full_path = os.path.join(CONFIG_DIR, override_path)
                with open(full_path, "r") as f:
                    override = yaml.safe_load(f)
                    config.update(override)
            except Exception as e:
                logger.warning(f"⚠️ Failed to load project firewall override from '{override_path}': {e}")
        elif isinstance(override_path, dict):
            config.update(override_path)

    # 4️⃣ Helper: convert VLAN(10) → actual subnet CIDR using resolved VLANs
    def resolve_cidr(value):
        if not isinstance(value, str) or "VLAN(" not in value:
            return value  # nothing to resolve
        for vlan in resolved_vlans or []:
            cidr = vlan.get("subnet")
            if not cidr:
                continue
            patterns = [f"VLAN({vlan['id']})", f"VLAN({vlan['name']})"]
            for pat in patterns:
                if pat in value:
                    return value.replace(pat, cidr)
        logger.warning(f"⚠️ Could not resolve VLAN reference in CIDR field: {value}")
        return value  # fallback unchanged

    # 5️⃣ Normalize each rule, resolving CIDRs only for inbound rules
    def resolve_rule(rule, resolve_vlan_refs=True):
        rule = deepcopy(rule)
        if resolve_vlan_refs:
            rule["srcCidr"] = resolve_cidr(rule.get("srcCidr", "any"))
            rule["destCidr"] = resolve_cidr(rule.get("destCidr", "any"))
        logger.debug(f"[FIREWALL] Resolved rule: {rule}")
        return rule

    # 6️⃣ Resolve rules: outbound can keep Meraki-native VLAN() syntax, inbound must resolve to CIDR
    outbound = [resolve_rule(r, resolve_vlan_refs=False) for r in config.get("outbound_rules", [])]
    inbound  = [resolve_rule(r, resolve_vlan_refs=True)  for r in config.get("inbound_rules", [])]

    # 7️⃣ Final output
    logger.info(f"🔥 Final resolved outbound rules: {outbound}")
    logger.info(f"🔥 Final resolved inbound rules: {inbound}")

    return {
        "outbound_rules": outbound,
        "inbound_rules": inbound
    }
# 📡 Resolve MX wireless config from common + project overrides
def resolve_mx_wireless(defaults, backend, project_overrides=None):
    config = {"defaults": {}, "ssids": []}

    # 1. Start with inline defaults fallback (rarely used, but keeps interface clean)
    if "mx_wireless" in defaults:
        config["ssids"] = defaults["mx_wireless"].get("ssids", [])

    # 2. Load common config (same shape as mx_ports)
    try:
        common_config = backend.get_mx_wireless()
        config["defaults"] = common_config.get("defaults", {})
        config["ssids"] = common_config.get("ssids", config["ssids"])
    except Exception as e:
        logger.warning(f"⚠️ Failed to load common mx_wireless.yaml: {e}")

    # 3. Apply project-level override
    if project_overrides:
        override_path = project_overrides.get("mx_wireless")
        if isinstance(override_path, str):
            try:
                full_path = os.path.join(CONFIG_DIR, override_path)
                with open(full_path, "r") as f:
                    override = yaml.safe_load(f)
                    config["ssids"] = override.get("ssids", config["ssids"])
                    config["defaults"].update(override.get("defaults", {}))
            except Exception as e:
                logger.warning(f"⚠️ Failed to load project mx_wireless override from '{override_path}': {e}")
        elif isinstance(override_path, dict):
            config["ssids"] = override_path.get("ssids", config["ssids"])
            config["defaults"].update(override_path.get("defaults", {}))

    return config

# 📎 Resolve fixed IP assignments and inject into matching VLANs
def resolve_fixed_assignments(fixed_assignments, resolved_vlans):
    import logging
    import ipaddress
    from copy import deepcopy
    logger = logging.getLogger(__name__)

    # 1️⃣ Build quick lookup by VLAN name
    vlan_map = {vlan["name"]: vlan for vlan in resolved_vlans}

    # 2️⃣ Initialize each with an empty fixedIpAssignments field
    for vlan in resolved_vlans:
        vlan["fixedIpAssignments"] = {}

    # 3️⃣ Assign IPs based on offset
    for vlan_name, mac_map in fixed_assignments.items():
        if vlan_name not in vlan_map:
            logger.warning(f"⚠️ Fixed assignment references unknown VLAN '{vlan_name}'")
            continue

        target_vlan = vlan_map[vlan_name]
        subnet = target_vlan.get("subnet")

        if not subnet:
            logger.warning(f"⚠️ VLAN '{vlan_name}' has no subnet — skipping fixed IPs.")
            continue

        net = ipaddress.ip_network(subnet)

        for mac, entry in mac_map.items():
            offset = entry.get("offset")
            if offset is None:
                logger.warning(f"⚠️ Missing offset for MAC {mac} in VLAN {vlan_name}")
                continue

            try:
                ip = str(net[offset])
            except Exception as e:
                logger.error(f"❌ Invalid offset {offset} in subnet {subnet}: {e}")
                continue

            target_vlan["fixedIpAssignments"][mac] = {
                "ip": ip,
                "name": entry.get("name", ""),
                "tags": entry.get("tags", []),
            }

    # ✅ Log final result
    for vlan in resolved_vlans:
        if vlan["fixedIpAssignments"]:
            logger.info(f"📌 Fixed IPs for VLAN {vlan['name']}: {vlan['fixedIpAssignments']}")

    return resolved_vlans

# 🔧 Resolve and merge all config layers: defaults → org → network → device
def resolve_project_configs(config_dir=CONFIG_DIR, backend=None):
    # 📦 Dynamic or injected backend resolver
    if backend is None:
        from backend.router import get_backend_for
    else:
        def get_backend_for(kind, _defaults=None):
            return backend

    # 📥 Load config fragments
    defaults_backend = get_backend_for("defaults")
    manifest_backend = get_backend_for("manifest", defaults_backend.get_defaults())
    devices_backend = get_backend_for("devices", defaults_backend.get_defaults())
    vlans_backend = get_backend_for("vlans", defaults_backend.get_defaults())
    firewall_backend = get_backend_for("firewall_rules", defaults_backend.get_defaults())
    static_routes_backend = get_backend_for("static_routes", defaults_backend.get_defaults())
    exclusions_backend = get_backend_for("exclusions", defaults_backend.get_defaults())

    defaults = defaults_backend.get_defaults()
    manifest = manifest_backend.get_manifest()
    raw_devices = devices_backend.get_devices()
    base_vlans = vlans_backend.get_vlans().get("vlans", [])
    exclusions = exclusions_backend.get_exclusions()

    # 🧯 Setup shared IPAM allocator
    ipam_cfg = defaults.get("ipam", {})
    ipam_supernet = ipam_cfg.get("supernet")
    if not ipam_supernet:
        raise ValueError("❌ IPAM 'supernet' must be defined in defaults.yaml")

    reserved_blocks = ipam_cfg.get("reserved", [])
    for cidr in reserved_blocks:
        ipaddress.ip_network(cidr, strict=False)  # validate

    alloc = ipam_cfg.get("allocation", {})
    default_network_prefix = int(alloc["network_prefix"])
    default_vlan_cidr = int(alloc["vlan_prefix"])

    allocator = IPAMAllocator(ipam_supernet, used_subnets=reserved_blocks)
    devices = flatten_devices(raw_devices)
    resolved = []

    for project in manifest.get("projects", []):
        project_name = project["name"]
        org_base = project["org_base_name"]
        project_slug = project.get("slug") or project_name.lower().replace(" ", "_")

        # 🔁 Load all fixed IPs across all networks in this project
        fixed_ip_backend = get_backend_for("fixed_assignments", defaults)
        fixed_ips_by_network_slug = fixed_ip_backend.get_fixed_assignments(project_slug)

        for net in project.get("networks", []):
            net_base = net["base_name"]
            network_slug = net.get("slug") or net_base.lower().replace(" ", "_")  # 👈 Static slug
            full_tag = f"{project_slug}-{network_slug}"

            # 🧰 Allocate fresh IPAM block
            network_block = allocator.allocate_network_block(default_network_prefix)

            # 🦰 Start with defaults, apply org and naming overrides
            net_config = deepcopy(defaults)
            net_config["organization"] = merge_dicts(
                net_config.get("organization", {}),
                project.get("organization", {})
            )
            if "naming" in net:
                net_config["naming"] = merge_dicts(
                    net_config.get("naming", {}),
                    net["naming"]
                )

            # 🌐 Allocate subnets per VLAN
            processed_vlans = []
            for vlan in base_vlans:
                vlan = deepcopy(vlan)
                cidr_hint = vlan.get("ipam", {}).get("cidr")
                prefixlen = int(cidr_hint.strip("/")) if cidr_hint else default_vlan_cidr

                logger.debug(f"[DEBUG] Allocating VLAN ID {vlan['id']} with prefix /{prefixlen} inside block {network_block}")
                subnet = allocator.allocate_vlan_subnet(network_block, vlan_id=vlan["id"], prefixlen=prefixlen) \
                         if default_network_prefix == 16 and prefixlen == 24 \
                         else allocator.allocate_subnet(prefixlen)

                vlan["subnet"] = subnet
                vlan["gatewayIp"] = str(ipaddress.ip_network(subnet)[1])
                processed_vlans.append(vlan)

            # 📎 Inject fixed IPs (only for this static network_slug)
            network_fixed_ips = fixed_ips_by_network_slug.get(network_slug, {})
            processed_vlans = resolve_fixed_assignments(network_fixed_ips, processed_vlans)

            # 📦 Assemble full config
            net_config["vlans"] = processed_vlans
            net_config["firewall"] = resolve_firewall_rules(
                defaults,
                backend,
                net.get("config", {}),
                processed_vlans
            )
            net_config["mx_static_routes"] = resolve_mx_static_routes(defaults, backend, net.get("config", {}), processed_vlans)["routes"]
            net_config["exclusions"] = exclusions
            net_config["fixed_assignments"] = network_fixed_ips
            net_config["mx_ports"] = resolve_mx_ports(defaults, backend, net.get("config", {}))
            net_config["mx_wireless"] = resolve_mx_wireless(defaults, backend, net.get("config", {}))

            resolved.append({
                "project_name": project_name,
                "org_base_name": org_base,
                "net_base_name": net_base,
                "full_tag": full_tag,
                "network_config": net_config,
            })

    return {
        "resolved_networks": resolved,
        "devices": devices,
    }
