from math import isclose

import pytest

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.datasets.campaigns import warmup_is_clean
from fedcampaign_emhi.datasets.preprocessing import complete_benign_horizons
from fedcampaign_emhi.domain.enums import OperatingPointState, ScientificOutcomeKind
from fedcampaign_emhi.emhi.sequential import (
    coalition_materially_active,
    distributed_support_predicate,
    first_global_stop_epoch,
    statistical_stop,
    trailing_support_window_client_ids,
    trailing_window_length,
    trailing_window_support_predicate,
)
from fedcampaign_emhi.emhi.thresholds import (
    calibrated_finite_horizon_outcome,
    clopper_pearson_one_sided_upper_bound,
    esr_threshold_from_arl_alpha,
    operating_point_unavailable_outcome,
    select_calibrated_threshold,
)
from fedcampaign_emhi.evaluation.benign_horizons import (
    horizons_are_nonoverlapping,
    sequential_stop_reset_epochs,
)
from fedcampaign_emhi.evaluation.campaign_replay import (
    campaign_replay_plan,
    operational_lead,
    statistical_lead,
)


def test_material_activity_uses_configured_threshold_inclusively() -> None:
    loaded = load_production_configuration()
    threshold = loaded.values.distributed_support.material_coalition_evidence_threshold
    assert threshold == 1.25
    assert coalition_materially_active(threshold, threshold) is True
    assert coalition_materially_active(1.2499, threshold) is False


def test_trailing_window_unions_distinct_clients_over_last_epochs() -> None:
    per_epoch = (("a", "b"), ("b", "c"), ("d",))
    assert trailing_support_window_client_ids(per_epoch, 5) == ("a", "b", "c", "d")
    assert trailing_support_window_client_ids(per_epoch, 2) == ("b", "c", "d")
    assert trailing_window_length(5, 3) == 3
    assert trailing_window_length(5, 9) == 5


def test_support_predicate_requires_minimum_distinct_clients_and_can_delay() -> None:
    loaded = load_production_configuration()
    minimum = loaded.values.distributed_support.minimum_clients
    window = loaded.values.distributed_support.trailing_window_epochs
    assert minimum == 2
    assert window == 5
    assert trailing_window_support_predicate((("a",), ("a",)), window, minimum) is False
    assert trailing_window_support_predicate((("a",), ("a", "b")), window, minimum) is True
    evidence = (2.0, 2.0, 2.0)
    supported = (False, True, True)
    delayed = first_global_stop_epoch(evidence, supported, 1.0)
    assert delayed == 1
    with pytest.raises(ValueError):
        trailing_support_window_client_ids((("a",),), 0)


def test_support_predicate_never_lowers_threshold() -> None:
    assert statistical_stop(4.0, 4.0, (), 2) is False
    assert distributed_support_predicate(("a", "b", "c"), 3) is True


def test_signed_theorem_route_threshold_is_reciprocal_of_arl_alpha() -> None:
    loaded = load_production_configuration()
    alpha = loaded.values.evidence.signed_theorem_sequential.arl_alpha
    assert alpha == 0.001
    derived = loaded.derived.signed_theorem_e_sr_threshold
    assert isclose(derived, 1000.0)
    assert esr_threshold_from_arl_alpha(alpha) == derived


def test_calibrated_finite_horizon_contract_and_selection() -> None:
    loaded = load_production_configuration()
    finite_horizon = loaded.values.evidence.calibrated_finite_horizon
    horizon_epochs = loaded.values.campaign.evaluation_horizon_epochs
    assert horizon_epochs == 60
    assert finite_horizon.target_pfa == 0.05
    assert finite_horizon.calibration_confidence == 0.95
    assert isclose(
        clopper_pearson_one_sided_upper_bound(0, 59, finite_horizon.calibration_confidence),
        1.0 - (1.0 - finite_horizon.calibration_confidence) ** (1.0 / 59),
        rel_tol=1e-12,
    )
    assert (
        clopper_pearson_one_sided_upper_bound(59, 59, finite_horizon.calibration_confidence) == 1.0
    )
    selected = select_calibrated_threshold(
        (10.0, 3.0, 20.0),
        (1, 0, 1),
        59,
        finite_horizon.calibration_confidence,
        finite_horizon.target_pfa,
    )
    assert selected == 3.0
    unavailable = calibrated_finite_horizon_outcome(None)
    assert unavailable.kind is ScientificOutcomeKind.OPERATING_POINT_UNAVAILABLE
    assert unavailable.operating_point_state is OperatingPointState.UNAVAILABLE
    assert unavailable.experiment_state.value == "Completed"
    assert not unavailable.is_implementation_error
    completed = calibrated_finite_horizon_outcome(10.0)
    assert completed.kind is ScientificOutcomeKind.COMPLETED_UNFAVORABLE
    assert completed.operating_point_state is OperatingPointState.AVAILABLE
    assert operating_point_unavailable_outcome().operating_point_state is (
        OperatingPointState.UNAVAILABLE
    )


def test_minimum_zero_false_stop_horizons_is_fifty_nine() -> None:
    loaded = load_production_configuration()
    assert loaded.derived.minimum_nonoverlapping_horizons_for_zero_false_stop == 59


def test_candidate_thresholds_evaluated_on_nonoverlapping_calibration_horizons() -> None:
    epochs = tuple(range(200, 200 + 180))
    horizons_a = complete_benign_horizons(epochs, 60)
    horizons_b = complete_benign_horizons(tuple(range(400, 400 + 120)), 60)
    all_horizons = horizons_a + horizons_b
    flat = [epoch for horizon in all_horizons for epoch in horizon.epoch_indexes]
    assert len(flat) == len(set(flat))
    assert horizons_are_nonoverlapping(horizons_a)
    assert sequential_stop_reset_epochs(horizons_a) == (200, 260, 320)


def test_threshold_is_never_modified_using_heldout_data() -> None:
    loaded = load_production_configuration()
    candidates = loaded.values.evidence.calibrated_finite_horizon.threshold_candidates
    calibration_counts = (0, 1, 1)
    selected = select_calibrated_threshold(
        candidates[:3],
        calibration_counts,
        59,
        loaded.values.evidence.calibrated_finite_horizon.calibration_confidence,
        loaded.values.evidence.calibrated_finite_horizon.target_pfa,
    )
    assert selected == candidates[0]
    heldout_counts = (5, 5, 5)
    assert (
        select_calibrated_threshold(
            candidates[:3],
            heldout_counts,
            59,
            loaded.values.evidence.calibrated_finite_horizon.calibration_confidence,
            loaded.values.evidence.calibrated_finite_horizon.target_pfa,
        )
        is None
    )


def test_campaign_replay_resets_state_and_computes_warmup_through_contexts() -> None:
    loaded = load_production_configuration()
    warmup_count = loaded.values.campaign.prestart_warmup_epochs
    horizon = loaded.values.campaign.evaluation_horizon_epochs
    plan = campaign_replay_plan(500, warmup_count, horizon)
    assert len(plan.warmup_epochs) == warmup_count
    assert max(plan.warmup_epochs) == 499
    assert min(plan.campaign_epochs) == 500
    assert len(plan.campaign_epochs) == horizon
    assert plan.global_state_reset is True
    assert plan.local_persistence_reset is True
    assert first_global_stop_epoch((2.0,), (True,), 1.0) == 0


def test_replay_warmup_must_be_clean() -> None:
    assert warmup_is_clean(()) is True
    assert warmup_is_clean((7,)) is False


def test_statistical_lead_formula() -> None:
    assert statistical_lead(9, 4) == 5.0
    assert statistical_lead(4, 4) == 0.0
    assert statistical_lead(3, 4) == -1.0


def test_operational_lead_adds_reference_latency_offset() -> None:
    loaded = load_production_configuration()
    seconds = loaded.values.time.real_data_epoch_seconds
    assert seconds == 60
    lead = operational_lead(10, 4, 120.0, seconds)
    assert lead == 4.0
    zero = operational_lead(10, 4, 0.0, seconds)
    assert zero == statistical_lead(10, 4)
    tie = operational_lead(5, 5, 300.0, seconds)
    assert tie == -5.0
