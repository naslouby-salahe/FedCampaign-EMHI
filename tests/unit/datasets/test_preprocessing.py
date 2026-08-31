import hashlib
import inspect
from math import log, log1p

import pytest

from fedcampaign_emhi.datasets.preprocessing import (
    apply_robust_scaler,
    chronological_benign_partitions,
    chronological_partition_lengths,
    common_benign_epoch_bounds,
    complete_horizon_count,
    detector_fit_sample_requirement_is_met,
    empty_epoch_feature_vector,
    epoch_feature_vector,
    event_type_hash_bucket,
    fit_robust_scaler,
    horizon_eligibility_state,
    inclusive_epoch_range,
    retain_first_chronological,
    shannon_entropy,
)
from fedcampaign_emhi.domain.enums import DatasetName, ExperimentState, SupportState
from fedcampaign_emhi.domain.types import (
    NormalizedEventToken,
    RecordCount,
    RetainedEvent,
    UnixTimestampSeconds,
)


def _event(
    timestamp_seconds: UnixTimestampSeconds,
    payload: NormalizedEventToken,
    unique_identifier: NormalizedEventToken | None = None,
    original_order: RecordCount = 0,
    event_type: NormalizedEventToken = "TCP::HTTP",
) -> RetainedEvent:
    return RetainedEvent(
        dataset_name=DatasetName.TON_IOT_NETWORK,
        client_id="10.0.0.1",
        timestamp_seconds=timestamp_seconds,
        event_type=event_type,
        payload=payload,
        unique_identifier=unique_identifier,
        original_order=original_order,
    )


def test_hash_mapping_uses_sha256_first_eight_bytes() -> None:
    event_type = "UNKNOWN_PROTO::UNKNOWN_SERVICE"
    bucket = event_type_hash_bucket(event_type, 64)
    digest = hashlib.sha256(event_type.encode("utf-8")).digest()
    assert bucket == int.from_bytes(digest[:8], "big") % 64
    protocol_event = "PROTOCOL::TCP"
    first = event_type_hash_bucket(protocol_event, 64)
    second = event_type_hash_bucket(protocol_event, 64)
    protocol_digest = hashlib.sha256(protocol_event.encode("utf-8")).digest()
    assert first == second
    assert first == int.from_bytes(protocol_digest[:8], "big") % 64


def test_duplicates_retain_first_chronological_and_count() -> None:
    events = (
        _event(20.0, "a", original_order=1),
        _event(10.0, "a", original_order=0),
        _event(10.0, "a", original_order=2),
    )
    outcome = retain_first_chronological(events)
    assert outcome.experiment_state is ExperimentState.READY
    assert outcome.duplicate_count == 1
    assert outcome.retained_events[0].original_order == 0
    assert "seed" not in inspect.signature(retain_first_chronological).parameters


def test_duplicate_identifiers_with_conflicting_payloads_are_invalid() -> None:
    events = (
        _event(10.0, "left", unique_identifier="flow-1", original_order=0),
        _event(11.0, "right", unique_identifier="flow-1", original_order=1),
    )
    outcome = retain_first_chronological(events)
    assert outcome.experiment_state is ExperimentState.INVALID
    assert outcome.retained_events == ()


def test_epoch_features_log1p_total_and_entropy() -> None:
    counts = (2, 0, 2)
    vector = epoch_feature_vector(counts)
    assert vector.log1p_bucket_counts == (log1p(2), log1p(0), log1p(2))
    assert vector.total_raw_event_count == 4
    expected = -((0.5 * log(0.5)) + (0.5 * log(0.5)))
    assert abs(vector.shannon_entropy - expected) < 1.0e-12
    empty = empty_epoch_feature_vector(3)
    assert empty.log1p_bucket_counts == (0.0, 0.0, 0.0)
    assert empty.total_raw_event_count == 0
    assert empty.shannon_entropy == 0.0
    assert shannon_entropy((0, 0, 0)) == 0.0


def test_common_interval_keeps_empty_epochs_and_fixed_partitions() -> None:
    bounds = common_benign_epoch_bounds(((0, 5), (0, 5), (1, 5)))
    assert bounds is not None
    assert bounds == (1, 5)
    epochs = inclusive_epoch_range(bounds[0], bounds[1])
    assert epochs == (1, 2, 3, 4, 5)
    lengths = chronological_partition_lengths(5, 0.2, 0.2, 0.2)
    partitions = chronological_benign_partitions(epochs, lengths)
    assert (
        partitions.detector_fit
        + partitions.nuisance_fit
        + (partitions.threshold_and_policy_calibration + partitions.heldout_benign)
        == epochs
    )
    assert "shuffle" not in inspect.signature(chronological_benign_partitions).parameters
    assert "random" not in inspect.signature(chronological_benign_partitions).parameters


def test_robust_scaler_uses_detector_fit_only() -> None:
    scaler = fit_robust_scaler((1.0, 2.0, 3.0, 4.0, 5.0), 1.0)
    later = apply_robust_scaler(scaler, (1.0, 5.0))
    assert later[0] < later[1]
    with pytest.raises(ValueError, match="non-finite"):
        apply_robust_scaler(scaler, (float("inf"),))


def test_horizon_eligibility_is_not_tested_without_rescue() -> None:
    assert complete_horizon_count(100, 3) == 33
    assert horizon_eligibility_state(10, 59) is SupportState.NOT_TESTED
    assert horizon_eligibility_state(59, 59) is SupportState.SUPPORTED
    assert not detector_fit_sample_requirement_is_met(0)
    assert detector_fit_sample_requirement_is_met(1)
    assert tuple(inspect.signature(horizon_eligibility_state).parameters) == (
        "complete_horizons",
        "required_horizons",
    )
