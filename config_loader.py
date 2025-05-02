import os
import yaml

CONFIG_DIR = "config"

def load_yaml_file(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_common_file(relative_path):
    path = os.path.join(CONFIG_DIR, "common", relative_path)
    return load_yaml_file(path)

def load_project_file(relative_path):
    path = os.path.join(CONFIG_DIR, "projects", relative_path)
    return load_yaml_file(path)

def load_devices_file():
    path = os.path.join(CONFIG_DIR, "devices", "devices.yaml")
    return load_yaml_file(path)

def load_manifest_file():
    path = os.path.join(CONFIG_DIR, "manifest.yaml")
    return load_yaml_file(path)

def load_defaults_file():
    path = os.path.join(CONFIG_DIR, "defaults.yaml")
    return load_yaml_file(path)

def load_all_configs():
    return {
        "defaults": load_defaults_file(),
        "manifest": load_manifest_file(),
        "devices": load_devices_file(),
    }