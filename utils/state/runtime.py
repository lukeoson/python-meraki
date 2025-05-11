import os
import json
from pathlib import Path

def get_runtime_state_file(project_slug):
    return Path(f"state/runtime/{project_slug}.json")

def save_runtime_state(project_slug, org_id, org_name, networks: dict):
    """
    Overwrites the runtime state file with the current run's deployment values.
    Supports one project/org per run with multiple named networks.
    `networks` should be a dict where key = network slug, value = dict with id & name.
    """
    runtime_file = get_runtime_state_file(project_slug)
    os.makedirs(runtime_file.parent, exist_ok=True)

    runtime_data = {
        "project_slug": project_slug,
        "org": {
            "org_id": org_id,
            "org_name": org_name
        },
        "networks": networks
    }

    with open(runtime_file, "w") as f:
        json.dump(runtime_data, f, indent=2)

def load_runtime_state(project_slug) -> dict:
    """
    Returns the current runtime state for the given project if the file exists.
    """
    runtime_file = get_runtime_state_file(project_slug)
    if runtime_file.exists():
        with open(runtime_file, "r") as f:
            return json.load(f)
    return {}

def get_org_id(project_slug) -> str | None:
    """
    Returns the org_id from the runtime state.
    """
    state = load_runtime_state(project_slug)
    return state.get("org", {}).get("org_id")

def get_network_id_by_slug(project_slug, slug: str) -> str | None:
    """
    Returns the network_id for the given network slug from the runtime state.
    """
    state = load_runtime_state(project_slug)
    return state.get("networks", {}).get(slug, {}).get("network_id")
