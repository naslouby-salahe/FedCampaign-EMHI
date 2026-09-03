import pytest

from fedcampaign_emhi.comparators.dependence import (
    cosine_equivalence_criterion,
    nrmse_equivalence_criterion,
    pfa_prerequisite_criterion,
    stopping_time_equivalence_criterion,
    target_coalition_for_order,
)
from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.evaluation.metrics import atom_cosine_similarity, atom_nrmse


def test_target_coalition_sizes() -> None:
    assert target_coalition_for_order(CoalitionOrder.ONE, 12) == 1
    assert target_coalition_for_order(CoalitionOrder.TWO, 12) == 2
    assert target_coalition_for_order(CoalitionOrder.THREE, 12) == 3
    with pytest.raises(ValueError):
        target_coalition_for_order(CoalitionOrder.THREE, 2)


def test_nrmse_criterion_requires_complete_ci_below_margin() -> None:
    loaded = load_production_configuration()
    margin = loaded.values.materiality.hofd_equivalence.atom_nrmse_upper_margin
    assert nrmse_equivalence_criterion(margin - 0.01, margin) is True
    assert nrmse_equivalence_criterion(margin, margin) is False
    assert nrmse_equivalence_criterion(margin + 0.01, margin) is False


def test_cosine_criterion_requires_minimum_similarity() -> None:
    loaded = load_production_configuration()
    minimum = loaded.values.materiality.hofd_equivalence.minimum_cosine_similarity
    assert cosine_equivalence_criterion(1.0, minimum) is True
    assert cosine_equivalence_criterion(minimum, minimum) is True
    assert cosine_equivalence_criterion(minimum - 0.001, minimum) is False


def test_stopping_time_criterion_requires_ci_inside_interval() -> None:
    loaded = load_production_configuration()
    interval = loaded.values.materiality.hofd_equivalence.stopping_time_difference_interval_epochs
    lower, upper = interval[0], interval[1]
    assert stopping_time_equivalence_criterion(lower, upper, lower, upper) is True
    assert stopping_time_equivalence_criterion(lower - 0.5, upper, lower, upper) is False
    assert stopping_time_equivalence_criterion(lower, upper + 0.5, lower, upper) is False


def test_null_pfa_prerequisite_before_equivalence() -> None:
    loaded = load_production_configuration()
    target = loaded.values.evidence.calibrated_finite_horizon.target_pfa
    assert pfa_prerequisite_criterion(target, target) is True
    assert pfa_prerequisite_criterion(target - 0.01, target) is True
    assert pfa_prerequisite_criterion(target + 0.01, target) is False


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


def test_atom_metrics_use_aligned_vector_geometry() -> None:
    emhi = ((1.0, 0.0), (0.0, 1.0))
    hofd = ((1.0, 0.0), (0.0, 1.0))
    assert atom_nrmse(emhi, hofd, 1e-12) == 0.0
    assert atom_cosine_similarity(emhi, hofd, 1e-12) == pytest.approx(1.0)
