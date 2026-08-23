from fedcampaign_emhi.analysis.statistics import (
    exact_sign_pattern,
    hodges_lehmann_shift,
    interval_establishes_equivalence,
    paired_difference,
    sign_flip_assignment_count,
)


def test_paired_seed_statistics_preserve_pairing() -> None:
    differences = paired_difference((4.0, 7.0, 10.0), (1.0, 3.0, 6.0))
    assert differences == (3.0, 4.0, 4.0)
    assert hodges_lehmann_shift(differences) == 3.75


def test_exact_sign_family_includes_zero_assignment() -> None:
    assert sign_flip_assignment_count(3) == 8
    assert exact_sign_pattern(0, 3) == (1, 1, 1)
    assert exact_sign_pattern(7, 3) == (-1, -1, -1)


def test_equivalence_requires_entire_interval_inside_region() -> None:
    assert interval_establishes_equivalence(-0.1, 0.1, -0.2, 0.2)
    assert not interval_establishes_equivalence(-0.3, 0.1, -0.2, 0.2)
