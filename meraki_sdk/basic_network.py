# meraki_sdk/network/basic_network.py
import logging

logger = logging.getLogger(__name__)

def ensure_network(dashboard, org_id, net_config):
    """
    Create a network if it doesn't already exist in the given org.
    """
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    for net in networks:
        if net['name'] == net_config['name']:
            logger.info(f"🔁 Reusing existing network '{net['name']}' ({net['id']}) in org {org_id}")
            return net['id']

    data = {
        "name": net_config['name'],
        "productTypes": net_config.get("productTypes", ["appliance", "camera", "cellularGateway"]),
        "timeZone": net_config.get("timeZone", "Europe/London"),
        "tags": net_config.get("tags", ["defaults-applied", "defaults-lab"]),
        "notes": net_config.get("notes", "default config has been applied without reference to config.json")
    }

    response = dashboard.organizations.createOrganizationNetwork(
    organizationId=org_id,
    **data
    )
    logger.info(f"🆕 Created network '{data['name']}' ({response['id']}) in org {org_id}")
    return response["id"]


def get_next_network_by_prefix(dashboard, org_id, network_base_name):
    """
    Return the first network whose name starts with the given base name.
    E.g., "Studio Lab", "Lab Site", etc.
    """
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    for net in networks:
        if net["name"].startswith(network_base_name):
            logger.info(f"🔍 Found network '{net['name']}' ({net['id']}) in org {org_id}")
            return net

    logger.warning(f"⚠️ No network found starting with '{network_base_name}' in org {org_id}")
    return None