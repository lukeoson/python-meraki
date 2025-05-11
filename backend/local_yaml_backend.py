# backend/local_yaml_backend.py

import yaml
from pathlib import Path
from backend.interface import BackendProvider

class LocalYAMLBackend(BackendProvider):
    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)

    def _load_yaml(self, relative_path):
        file_path = self.config_dir / relative_path
        with open(file_path, "r") as f:
            return yaml.safe_load(f)

    def get_devices(self):
        return self._load_yaml("devices/devices.yaml")

    def get_vlans(self):
        return self._load_yaml("common/vlans/mx_vlans.yaml")
    
    def get_mx_ports(self):
        return self._load_yaml("common/ports/mx_ports.yaml")

    def get_mx_ports_project(self, project_name):
        return self._load_yaml(f"projects/{project_name}/ports/mx_ports.yaml")

    def get_firewall_rules(self):
        return self._load_yaml("common/firewall/mx_firewall.yaml")

    def get_mx_static_routes(self):
        return self._load_yaml("common/routes/mx_static.yaml")
    
    def get_mx_autovpn_common(self):
        return self._load_yaml("common/vpn/mx_autovpn.yaml")

    def get_mx_autovpn_project(self, project_name):
        return self._load_yaml(f"projects/{project_name}/vpn/mx_autovpn.yaml")

    def get_fixed_assignments(self, project_name):
        return self._load_yaml(f"projects/{project_name}/fixed_ip_assignments.yaml")

    def get_exclusions(self):
        return self._load_yaml("common/exclusion_rules.yaml")

    def get_manifest(self):
        return self._load_yaml("manifest.yaml")

    def get_defaults(self):
        return self._load_yaml("defaults.yaml")
    
    def get_mx_wireless(self):
        return self._load_yaml("common/wireless/mx_wireless.yaml")
    

