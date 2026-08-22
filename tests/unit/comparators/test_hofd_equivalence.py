import pytest

from fedcampaign_emhi.comparators.hofd_equivalence import (
    cosine_equivalence_gate,
    enumerate_hofd_equivalence_plan,
    hofd_equivalence_support_levels,
    nrmse_equivalence_gate,
    pfa_prerequisite_gate,
    stopping_time_equivalence_gate,
    target_coalition_for_order,
)
from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import CoalitionOrder


def test_plan_reads_every_value_from_authoritative_configuration() -> None:
    loaded = load_production_configuration()
    plan = enumerate_hofd_equivalence_plan(loaded.values)
    experiment = loaded.values.experiments.exclusion_matched_hofd_equivalence
    assert plan.primary_client_count == (
        loaded.values.experiments.pure_order_separation_validation.primary_client_count
    )
    assert plan.methods == tuple(method for method in experiment.methods)
    assert plan.context_cell_count == experiment.context_cell_count == 1
    assert plan.support_levels == tuple(experiment.primary_support_levels)
    assert plan.heldout_samples_per_context_seed == (
        loaded.values.synthetic.sample_sizes.hofd_equivalence_heldout_samples_per_context_seed
    )


def test_plan_seed_namespaces_are_separate() -> None:
    loaded = load_production_configuration()
    plan = enumerate_hofd_equivalence_plan(loaded.values)
    randomness = loaded.values.randomness
    assert plan.development_seed_count == len(randomness.synthetic_development_roots)
    assert plan.confirmatory_seed_count == len(randomness.synthetic_confirmatory_roots)


def test_support_levels_match_configured_grid() -> None:
    loaded = load_production_configuration()
    levels = hofd_equivalence_support_levels(loaded.values)
    declared = loaded.values.support_grids.hofd_equivalence_samples_per_context
    for level in levels:
        assert level in declared


def test_target_coalition_sizes() -> None:
    assert target_coalition_for_order(CoalitionOrder.ONE, 12) == 1
    assert target_coalition_for_order(CoalitionOrder.TWO, 12) == 2
    assert target_coalition_for_order(CoalitionOrder.THREE, 12) == 3
    with pytest.raises(ValueError):
        target_coalition_for_order(CoalitionOrder.THREE, 2)


def test_nrmse_gate_requires_complete_ci_below_margin() -> None:
    loaded = load_production_configuration()
    margin = loaded.values.claim_materiality.hofd_equivalence.atom_nrmse_upper_margin
    assert nrmse_equivalence_gate(margin - 0.01, margin) is True
    assert nrmse_equivalence_gate(margin, margin) is False
    assert nrmse_equivalence_gate(margin + 0.01, margin) is False


def test_cosine_gate_requires_minimum_similarity() -> None:
    loaded = load_production_configuration()
    minimum = loaded.values.claim_materiality.hofd_equivalence.minimum_cosine_similarity
    assert cosine_equivalence_gate(1.0, minimum) is True
    assert cosine_equivalence_gate(minimum, minimum) is True
    assert cosine_equivalence_gate(minimum - 0.001, minimum) is False


def test_stopping_time_gate_requires_ci_inside_interval() -> None:
    loaded = load_production_configuration()
    interval = (
        loaded.values.claim_materiality.hofd_equivalence.stopping_time_difference_interval_epochs
    )
    lower, upper = interval[0], interval[1]
    assert stopping_time_equivalence_gate(lower, upper, lower, upper) is True
    assert stopping_time_equivalence_gate(lower - 0.5, upper, lower, upper) is False
    assert stopping_time_equivalence_gate(lower, upper + 0.5, lower, upper) is False


def test_null_pfa_prerequisite_before_equivalence() -> None:
    loaded = load_production_configuration()
    target = loaded.values.evidence.calibrated_finite_horizon.target_pfa
    assert pfa_prerequisite_gate(target, target) is True
    assert pfa_prerequisite_gate(target - 0.01, target) is True
    assert pfa_prerequisite_gate(target + 0.01, target) is False


def test_all_coalition_orders_covered_by_target_rule() -> None:
    loaded = load_production_configuration()
    client_count = loaded.values.experiments.pure_order_separation_validation.primary_client_count
    maximum = loaded.values.study.maximum_coalition_order
    sizes = {
        target_coalition_for_order(order, client_count)
        for order in CoalitionOrder
        if int(order) <= maximum
    }
    assert sizes == {1, 2, 3}
