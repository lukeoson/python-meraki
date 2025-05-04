# meraki_sdk/logging/state.py

import os
import json
import datetime
import subprocess

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │ 🧠 Intended State                                                           │
# └─────────────────────────────────────────────────────────────────────────────┘
# This module captures the resolved configuration *before* it's pushed to Meraki.
# 
# The "intended state" is built by merging:
#   - global defaults (defaults.yaml)
#   - common fragments (e.g., vlans.yaml, firewall_rules.yaml)
#   - project-level overrides (projects/*.yaml)
#   - dynamically allocated IPAM subnets
#
# This config is assembled by `resolve_project_configs()` and passed into:
#   - `setup_network()` for Meraki network creation
#   - `setup_devices()` for device provisioning
#
# Saving this state allows us to:
#   - debug and inspect what was *supposed* to happen
#   - later build a comparison engine vs the *actual* Meraki state
#   - support dry-runs, auditing, and config assurance pipelines
#
# Output files go here:
#   - `state/intended_state/intended-{safe_org_name}.json`
#
# NOTE: This is not fetched from Meraki—it’s our *local intent*.

def get_git_commit_hash():
    """
    Attempts to retrieve the current Git commit hash to tag the state file.
    Falls back to 'unknown' if not in a Git repo or on error.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return result.stdout.decode("utf-8").strip()
    except Exception:
        return "unknown"

def save_intended_state(config, org_name):
    """
    Dumps the full resolved config for this org as an 'intended state' JSON file.
    
    📁 These files represent the declarative intent behind your infrastructure.
    They are stored under: state/intended_state/
    
    ✨ Each file is uniquely named using:
      - the sanitized org name (no spaces/dashes)
      - a UTC timestamp for uniqueness
      - the current Git commit hash (if available) for traceability
    """
    # Sanitize org name → lowercase, no spaces or dashes
    safe_name = org_name.lower().replace(" ", "").replace("-", "")

    # Generate timestamp and Git hash
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    git_hash = get_git_commit_hash()

    # Build filename: e.g., intended-percystreet007-20240502-132210-ab12cd3.json
    filename = f"intended-{safe_name}-{timestamp}-{git_hash[:7]}.json"
    folder = "state/intended_state"
    os.makedirs(folder, exist_ok=True)

    # Save the config as pretty JSON
    path = os.path.join(folder, filename)
    with open(path, "w") as f:
        json.dump(config, f, indent=2)

    return path  # Optionally used for logging