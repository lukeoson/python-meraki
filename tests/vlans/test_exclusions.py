# tests/network/vlans/test_exclusions.py

import pytest
from meraki_sdk.network.vlans.exclusions import get_vlan_exclusion, generate_exclusion_ranges

def test_generate_exclusion_ranges_basic():
    subnet = "10.0.0.0/24"
    ranges = generate_exclusion_ranges(subnet, exclusion_ratio=0.25)
    assert isinstance(ranges, list)
    assert len(ranges) == 1
    assert "start" in ranges[0]
    assert "end" in ranges[0]
    assert "comment" in ranges[0]

def test_get_vlan_exclusion_default_ratio():
    vlan = {"name": "TestVLAN", "subnet": "10.10.10.0/24"}
    result = get_vlan_exclusion(vlan)
    assert isinstance(result, list)
    assert result[0]["start"].startswith("10.10.10.")
    assert result[0]["end"].startswith("10.10.10.")

def test_get_vlan_exclusion_with_override():
    vlan = {"name": "MGMT", "subnet": "192.168.1.0/24"}
    overrides = {"MGMT": 0.5}
    result = get_vlan_exclusion(vlan, per_vlan_overrides=overrides)
    assert isinstance(result, list)
    # Expect more addresses reserved due to 50%
    assert "50%" in result[0]["comment"]

def test_get_vlan_exclusion_missing_subnet():
    vlan = {"name": "BrokenVLAN"}
    with pytest.raises(ValueError, match="missing 'subnet'"):
        get_vlan_exclusion(vlan)