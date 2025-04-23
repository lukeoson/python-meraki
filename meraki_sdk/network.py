# meraki_sdk/network.py

def ensure_network(dashboard, org_id, net_config):
    """
    Create a network if it doesn't already exist in the given org.
    """
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    for net in networks:
        if net['name'] == net_config['name']:
            return net['id']

    response = dashboard.organizations.createOrganizationNetwork(
        organizationId=org_id,
        name=net_config['name'],
        productTypes=net_config.get("productTypes", ["appliance", "camera", "cellularGateway"]),
        timeZone=net_config.get("timeZone", "Europe/London"),
        tags=net_config.get("tags", ["studio", "lab"]),
        notes=net_config.get("notes", "")
    )
    return response['id']


def get_studio_lab_network(dashboard, org_id):
    """
    Return the Studio Lab network from a given organization.
    """
    networks = dashboard.organizations.getOrganizationNetworks(org_id)
    return next((n for n in networks if n["name"].startswith("Studio Lab")), None)