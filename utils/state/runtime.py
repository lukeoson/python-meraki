import os
import json
from pathlib import Path

RUNTIME_STATE_FILE = Path("state/runtime.json")


def save_runtime_state(org_id, org_name, network_id, network_name):
    """
    Updates the runtime state file with the latest deployment values.
    Organizes data by org_id and supports multiple networks under each org.
    """
    os.makedirs(RUNTIME_STATE_FILE.parent, exist_ok=True)
    if RUNTIME_STATE_FILE.exists():
        with open(RUNTIME_STATE_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}

    org_entry = data.get(org_id, {
        "org_name": org_name,
        "networks": []
    })

    # Avoid duplicating the same network
    existing_names = [n["network_name"] for n in org_entry["networks"]]
    if network_name not in existing_names:
        org_entry["networks"].append({
            "network_id": network_id,
            "network_name": network_name
        })

    data[org_id] = org_entry

    with open(RUNTIME_STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)


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
    return state.get("org_id")


def get_network_id(org_id: str, network_name: str) -> str | None:
    """
    Retrieves a network_id for the given network_name under the specified org_id.
    """
    state = load_runtime_state()
    org_entry = state.get(org_id)
    if not org_entry:
        return None
    for network in org_entry.get("networks", []):
        if network["network_name"] == network_name:
            return network["network_id"]
    return None


def get_network_id_by_name(network_name: str) -> str | None:
    """
    Returns the network_id for the given network_name from the runtime state.
    """
    state = load_runtime_state()
    if state.get("network_name") == network_name:
        return state.get("network_id")
    return None
