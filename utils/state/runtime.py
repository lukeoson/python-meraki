import os
import json
from pathlib import Path

RUNTIME_STATE_FILE = Path("state/runtime.json")


def save_runtime_state(project_slug, org_id, org_name, networks: dict):
    """
    Overwrites the runtime state file with the current run's deployment values.
    Supports one project/org per run with multiple named networks.
    `networks` should be a dict where key = network slug, value = dict with id & name.
    """
    os.makedirs(RUNTIME_STATE_FILE.parent, exist_ok=True)

    runtime_data = {
        "project_slug": project_slug,
        "org": {
            "org_id": org_id,
            "org_name": org_name
        },
        "networks": networks
    }

    with open(RUNTIME_STATE_FILE, "w") as f:
        json.dump(runtime_data, f, indent=2)


def load_runtime_state() -> dict:
    """
    Returns the current runtime state if the file exists.
    """
    if RUNTIME_STATE_FILE.exists():
        with open(RUNTIME_STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def get_org_id() -> str | None:
    """
    Returns the org_id from the runtime state.
    """
    state = load_runtime_state()
    return state.get("org", {}).get("org_id")


def get_network_id_by_slug(slug: str) -> str | None:
    """
    Returns the network_id for the given network slug from the runtime state.
    """
    state = load_runtime_state()
    return state.get("networks", {}).get(slug, {}).get("network_id")
