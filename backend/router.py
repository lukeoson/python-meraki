# backend/router.py

from backend.interface import BackendProvider
from backend.local_yaml_backend import LocalYAMLBackend

# Future: add imports for NetBoxBackend, InfraHubBackend here

PROVIDERS = {
    "local": LocalYAMLBackend(),
    # "netbox": NetBoxBackend(),
    # "infrahub": InfraHubBackend(),
}

def get_backend_for(resource_name: str, defaults: dict) -> BackendProvider:
    """
    Returns the correct backend provider for a given resource.
    Looks for overrides in `defaults["backend_providers"]`.
    """
    config = defaults.get("backend_providers", {})
    override = config.get("overrides", {}).get(resource_name)
    provider_name = override or config.get("default", "local")
    return PROVIDERS[provider_name]