# meraki_sdk/network.py
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
        "productTypes": net_config.get("productTypes", ["combined"]),
        "timeZone": net_config.get("timeZone", "Europe/London"),
        "tags": net_config.get("tags", ["defaults-applied", "defaults-lab"]),
        "notes": net_config.get("notes", "default config has been applied without reference to config.json")
    }

    response = dashboard.organizations.createOrganizationNetwork(org_id, data)
    logger.info(f"🆕 Created network '{data['name']}' ({response['id']}) in org {org_id}")
    return response["id"]


def get_studio_lab_network(dashboard, org_id):
    """
    Return the first network named 'Studio Lab *' in the given organization.
    """
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    for net in networks:
        if net["name"].startswith("Studio Lab"):
            logger.info(f"🔍 Found Studio Lab network '{net['name']}' ({net['id']}) in org {org_id}")
            return net

    logger.warning(f"⚠️ No Studio Lab network found in org {org_id}")
    return None