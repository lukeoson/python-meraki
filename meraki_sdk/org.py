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


def get_previous_percy_org(orgs):
    """
    Return the most recent Percy Street org before the newly created one.
    If only one exists, assume that is the previous.
    """
    percy_orgs = [
        o for o in orgs
        if o["name"].startswith("Percy Street") and o["name"].split()[-1].isdigit()
    ]
    percy_orgs_sorted = sorted(percy_orgs, key=lambda o: int(o["name"].split()[-1]))

    if percy_orgs_sorted:
        return percy_orgs_sorted[-1]
    return None






