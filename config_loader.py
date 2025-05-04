import os
import yaml
import re

CONFIG_DIR = "config"


def check_unresolved(data):
    if re.search(r"\$\{\w+\}", str(data)):
        raise ValueError("Unresolved environment variables found in config.")

def resolve_env_vars(data):
    if isinstance(data, dict):
        return {k: resolve_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [resolve_env_vars(i) for i in data]
    elif isinstance(data, str):
        return re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), m.group(0)), data)
    return data

def load_yaml_file(path):
    with open(path, "r") as f:
        raw = yaml.safe_load(f)
        resolved = resolve_env_vars(raw)
        check_unresolved(resolved)
        return resolved

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