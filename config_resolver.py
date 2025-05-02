import os
import yaml
import ipaddress
import logging
from copy import deepcopy
from ipam.allocator import IPAMAllocator
from backend.router import get_backend_for
from config_loader import load_common_file

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

    # Load from defaults
    if "mx_ports" in defaults:
        config["ports"] = defaults["mx_ports"]

    # Merge common
    try:
        ports_path = os.path.join("common", "ports", "mx_ports.yaml")
        common_config = load_common_file("ports/mx_ports.yaml")
        config["defaults"] = common_config.get("defaults", {})
        config["ports"] = common_config.get("ports", config["ports"])
    except Exception as e:
        logger.warning(f"⚠️ Failed to load common mx_ports.yaml: {e}")

    # Merge project-level override
    if project_overrides:
        override_ports = project_overrides.get("mx_ports")
        if override_ports:
            config["ports"] = override_ports

    return config

# 🔧 Resolve and merge all config layers: defaults → org → network → device
def resolve_project_configs(config_dir=CONFIG_DIR, backend=None):
    # 📦 Determine backend resolver function (dynamic or fixed)
    if backend is None:
        from backend.router import get_backend_for
    else:
        def get_backend_for(kind, _defaults=None):
            return backend

    # 🗱️ Load all config fragments using backend abstraction
    defaults_backend = get_backend_for("defaults")
    defaults = defaults_backend.get_defaults()

    manifest_backend = get_backend_for("manifest", defaults)
    devices_backend = get_backend_for("devices", defaults)
    vlans_backend = get_backend_for("vlans", defaults)
    firewall_backend = get_backend_for("firewall_rules", defaults)
    static_routes_backend = get_backend_for("static_routes", defaults)
    exclusions_backend = get_backend_for("exclusions", defaults)

    manifest = manifest_backend.get_manifest()
    raw_devices = devices_backend.get_devices()
    devices = flatten_devices(raw_devices)
    vlans_raw = vlans_backend.get_vlans()
    base_vlans = vlans_raw.get("vlans", [])
    firewall_rules = firewall_backend.get_firewall_rules()
    static_routes = static_routes_backend.get_static_routes()
    exclusions = exclusions_backend.get_exclusions()

    # 🧯 Setup shared IPAM allocator once for the entire config resolution process
    ipam_cfg = defaults.get("ipam", {})
    ipam_supernet = ipam_cfg.get("supernet")
    if not ipam_supernet:
        raise ValueError("❌ IPAM 'supernet' must be defined in defaults.yaml")
    
    # 🧱 Preload reserved space before allocator is created
    reserved_blocks = ipam_cfg.get("reserved", [])
    for cidr in reserved_blocks:
        ipaddress.ip_network(cidr, strict=False)  # validate early

    allocation = ipam_cfg.get("allocation", {})
    try:
        default_on_prem_prefix = int(allocation["on_prem_prefix"])
        default_network_prefix = int(allocation["network_prefix"])
        default_vlan_cidr = int(allocation["vlan_prefix"])
    except KeyError as e:
        raise ValueError(f"❌ Missing IPAM allocation setting: {e}")

    # ✅ Shared allocator — so subnets don’t overlap across networks
    allocator = IPAMAllocator(ipam_supernet, used_subnets=reserved_blocks)

    resolved = []

    for project in manifest.get("projects", []):
        project_name = project["name"]
        org_base = project["org_base_name"]
        fixed_ip_backend = get_backend_for("fixed_assignments", defaults)
        project_slug = project.get("slug") or project_name.lower().replace(" ", "_")
        fixed_ips = fixed_ip_backend.get_fixed_assignments(project_slug)

        for net in project.get("networks", []):
            net_base = net["base_name"]
            network_slug = net.get("slug") or net_base.lower().replace(" ", "_")
            full_tag = f"{project_slug}-{network_slug}"

            # 🧰 Allocate a fresh block for this network
            network_block = allocator.allocate_network_block(default_network_prefix)

            # 🦰 Start with full defaults, then layer on overrides
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

            # 🌐 Dynamic IPAM logic: assign new subnets per VLAN
            processed_vlans = []
            for vlan in base_vlans:
                vlan = deepcopy(vlan)
                cidr_hint = vlan.get("ipam", {}).get("cidr")
                prefixlen = int(cidr_hint.strip("/")) if cidr_hint else default_vlan_cidr

                logger.debug(f"[DEBUG] Allocating VLAN ID {vlan['id']} with prefix /{prefixlen} inside network block {network_block}")

                # 🧠 If we're in /16 + /24 mode, use VLAN ID-based 3rd octet mapping
                if default_network_prefix == 16 and prefixlen == 24:
                    subnet = allocator.allocate_vlan_subnet(network_block, vlan_id=vlan["id"], prefixlen=prefixlen)
                else:
                    subnet = allocator.allocate_subnet(prefixlen)

                vlan["subnet"] = subnet
                vlan["gatewayIp"] = str(ipaddress.ip_network(subnet)[1])
                processed_vlans.append(vlan)

            # 📦 Merge remaining config blocks
            net_config["vlans"] = processed_vlans
            mx_ports_config = resolve_mx_ports(defaults, backend, project.get("overrides", {}))
            net_config["mx_ports"] = mx_ports_config
            net_config["firewall_rules"] = firewall_rules
            net_config["static_routes"] = static_routes
            net_config["exclusions"] = exclusions
            net_config["fixed_assignments"] = fixed_ips

            # ✅ Append fully merged network config
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
