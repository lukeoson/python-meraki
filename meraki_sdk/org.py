import re


def get_next_sequence_name(items, base_name):
    """
    Given a list of Meraki organizations (or similar items), return the next
    available name and sequence number for a new org based on the base name.
    E.g., Percy Street 003 → Percy Street 004
    """
    pattern = re.compile(rf"{re.escape(base_name)} (\d+)")
    numbers = [
        int(m.group(1)) for item in items
        if (m := pattern.search(item["name"]))
    ]
    next_seq = max(numbers, default=-1) + 1
    return f"{base_name} {next_seq:03d}", next_seq


def get_previous_org(orgs, org_base_name):
    """
    Return the most recent org matching the base name before the newly created one.
    Expects names like 'Percy Street 001', 'Percy Street 002', etc.
    """
    matching_orgs = [
        o for o in orgs
        if o["name"].startswith(org_base_name) and o["name"].split()[-1].isdigit()
    ]
    sorted_orgs = sorted(matching_orgs, key=lambda o: int(o["name"].split()[-1]))

    return sorted_orgs[-1] if sorted_orgs else None
