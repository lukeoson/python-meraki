import os
import json

CONFIG_DIR = "config"

def load_config_file(file_name):
    path = os.path.join(CONFIG_DIR, file_name)
    with open(path, "r") as f:
        return json.load(f)

def load_all_configs():
    return {
        "base": load_config_file("base.json"),
        "vlans": load_config_file("vlans.json"),
        #"firewall": load_config_file("firewall.json"),
        "devices": load_config_file("devices.json"),
        #"dhcp": load_config_file("dhcp.json")
    }