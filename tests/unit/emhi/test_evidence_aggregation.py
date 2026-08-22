import inspect
from math import exp

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.domain.enums import EvidencePath
from fedcampaign_emhi.emhi.evidence import (
    OPERATIONAL_EVIDENCE_COMPENSATOR,
    across_order_aggregate,
    clip_statistic,
    conditional_e_detector_path,
    euclidean_norm,
    locked_signed_compensator,
    operational_evidence_factor,
    operational_norm_reference_quantile,
    polynomial_signed_direction,
    primary_real_data_evidence_path,
    signed_conditional_null_holds,
    signed_direction_is_fixed_before_evaluation,
    signed_evidence_factor,
    signed_statistic,
    signed_theorem_compensator,
    within_order_aggregate,
)
from fedcampaign_emhi.emhi.sequential import (
    first_global_stop_epoch,
    initial_global_state,
    next_global_state,
    statistical_stop,
    threshold_predicate,
)


def test_signed_statistic_projects_and_clips() -> None:
    direction = polynomial_signed_direction(4, 1.0)
    assert direction == (1.0, 0.0, 0.0, 0.0)
    assert signed_direction_is_fixed_before_evaluation(direction)
    atom = (2.0, 9.0, -3.0, 1.0)
    assert signed_statistic(atom, direction, 1.0) == 1.0
    negative = polynomial_signed_direction(2, -2.0)
    assert negative == (-1.0, 0.0)
    assert signed_statistic((0.5, 8.0), negative, 1.0) == -0.5
    assert signed_conditional_null_holds(0.0)
    assert not signed_conditional_null_holds(0.1)


def test_signed_factor_matches_independent_exponent() -> None:
    loaded = load_production_configuration()
    clip_bound = loaded.values.evidence.clip_bound
    bet_lambda = loaded.values.evidence.bet_lambda
    compensator = signed_theorem_compensator(clip_bound, bet_lambda)
    assert compensator == 0.125
    assert locked_signed_compensator() == 0.125
    statistic = clip_statistic(1.0, clip_bound)
    expected = exp(bet_lambda * statistic - (bet_lambda**2) * ((2.0 * clip_bound) ** 2) / 8.0)
    assert signed_evidence_factor(1.0, clip_bound, bet_lambda) == expected
    assert conditional_e_detector_path() is EvidencePath.SIGNED_THEOREM
    assert primary_real_data_evidence_path() is EvidencePath.OPERATIONAL_NORM


def test_operational_norm_uses_vector_l2_and_fixed_compensator() -> None:
    atoms = ((3.0, 4.0), (0.0, 0.0))
    reference = operational_norm_reference_quantile(atoms, 0.5)
    assert reference == 2.5
    assert euclidean_norm((3.0, 4.0)) == 5.0
    factor = operational_evidence_factor((3.0, 4.0), 5.0, 1.0e-06, 1.0, 0.5)
    assert factor == exp(0.5 * 0.0 - OPERATIONAL_EVIDENCE_COMPENSATOR)
    assert OPERATIONAL_EVIDENCE_COMPENSATOR == 0.125
    wide_clip = operational_evidence_factor((3.0, 4.0), 1.0, 1.0e-06, 2.0, 0.5)
    assert wide_clip == exp(0.5 * 2.0 - 0.125)


def test_hierarchical_aggregation_is_equal_weight_mean() -> None:
    assert within_order_aggregate(()) == 1.0
    assert within_order_aggregate((2.0, 4.0)) == 3.0
    assert across_order_aggregate((1.0, 3.0, 5.0)) == 3.0
    source = inspect.getsource(within_order_aggregate) + inspect.getsource(across_order_aggregate)
    assert "prod" not in source
    assert "*" not in source or "sum" in source


def test_sequential_recursion_and_statistical_stop_ignore_local_policy() -> None:
    assert initial_global_state() == 0.0
    state = next_global_state(0.0, 2.0)
    assert state == 2.0
    state = next_global_state(state, 1.5)
    assert state == 4.5
    assert threshold_predicate(4.5, 4.0)
    assert statistical_stop(4.5, 4.0, ("a", "b"), 2)
    assert not statistical_stop(4.5, 4.0, ("a",), 2)
    stop = first_global_stop_epoch((1.0, 2.0, 2.0), (False, True, True), 2.0)
    assert stop == 1
    assert "local" not in inspect.signature(next_global_state).parameters
    assert "local" not in inspect.signature(first_global_stop_epoch).parameters
    assert "policy" not in inspect.signature(statistical_stop).parameters
