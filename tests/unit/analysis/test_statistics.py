from fedcampaign_emhi.analysis.statistics import (
    exact_sign_pattern,
    hodges_lehmann_shift,
    interval_establishes_equivalence,
    mean_bca_one_sided_lower_bound,
    one_sided_synthetic_sign_flip_p_value,
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


def test_one_sided_synthetic_sign_flip_uses_exact_family_when_feasible() -> None:
    assert one_sided_synthetic_sign_flip_p_value((1.0, 1.0), 4, 10, 7) == 0.25


def test_one_sided_synthetic_sign_flip_is_deterministic_when_monte_carlo_is_required() -> None:
    first = one_sided_synthetic_sign_flip_p_value((1.0,) * 5, 4, 20, 7)
    second = one_sided_synthetic_sign_flip_p_value((1.0,) * 5, 4, 20, 7)

    assert first == second
    assert 0.0 < first <= 1.0


def test_one_sided_bca_lower_bound_uses_the_declared_confidence_tail() -> None:
    lower = mean_bca_one_sided_lower_bound((1.0, 2.0, 3.0), 0.95, 1000, 11)

    assert lower <= 2.0
    assert mean_bca_one_sided_lower_bound((2.0, 2.0), 0.95, 10, 11) == 2.0
