from fedcampaign_emhi.emhi.contexts import exact_exclusion_members


def test_exact_exclusion_uses_complement_only() -> None:
    selected = ("c1", "c2", "c3", "c4", "c5", "c6")
    coalition = ("c1", "c2", "c3")
    assert exact_exclusion_members(selected, coalition) == ("c4", "c5", "c6")
