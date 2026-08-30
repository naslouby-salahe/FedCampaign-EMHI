import hashlib
from collections import UserDict
from math import floor, isfinite, log, log1p

import numpy as np
from numpy.typing import NDArray

from fedcampaign_emhi.domain.enums import ClaimState, DatasetName, ExperimentState
from fedcampaign_emhi.domain.types import (
    BenignHorizon,
    Boolean,
    ChronologicalBenignPartitions,
    ChronologicalPartitionLengths,
    ClientId,
    DeduplicationOutcome,
    EpochCount,
    EpochFeatureVector,
    EpochIndexValue,
    FiniteFloat,
    HashBucketCount,
    NormalizedEventToken,
    NumericalFloor,
    Probability,
    RecordCount,
    RetainedEvent,
    RobustScaler,
    SignedInt,
    UnixTimestampSeconds,
)


def chronological_partition_lengths(
    common_benign_epoch_count: EpochCount,
    detector_fit_fraction: Probability,
    nuisance_fit_fraction: Probability,
    threshold_fraction: Probability,
) -> ChronologicalPartitionLengths:
    detector_fit = floor(detector_fit_fraction * common_benign_epoch_count)
    nuisance_fit = floor(nuisance_fit_fraction * common_benign_epoch_count)
    threshold = floor(threshold_fraction * common_benign_epoch_count)
    used = detector_fit + nuisance_fit + threshold
    if used > common_benign_epoch_count:
        raise ValueError("configured partition fractions exceed the common benign epoch count")
    return ChronologicalPartitionLengths(
        detector_fit=detector_fit,
        nuisance_fit=nuisance_fit,
        threshold_and_policy_calibration=threshold,
        heldout_benign=common_benign_epoch_count - used,
    )


def event_type_hash_bucket(
    event_type: NormalizedEventToken, bucket_count: HashBucketCount
) -> SignedInt:
    if bucket_count <= 0:
        raise ValueError("bucket_count must be positive")
    digest = hashlib.sha256(event_type.encode("utf-8")).digest()
    identity = int.from_bytes(digest[:8], "big")
    return identity % bucket_count


def retain_first_chronological(
    events: tuple[RetainedEvent, ...],
) -> DeduplicationOutcome:
    ordered = tuple(
        sorted(events, key=lambda event: (event.timestamp_seconds, event.original_order))
    )
    retained: list[RetainedEvent] = []
    identified: UserDict[NormalizedEventToken, RetainedEvent] = UserDict()
    anonymous: set[
        tuple[
            DatasetName, ClientId, UnixTimestampSeconds, NormalizedEventToken, NormalizedEventToken
        ]
    ] = set()
    duplicate_count = 0
    for event in ordered:
        if event.unique_identifier is not None:
            existing = identified.get(event.unique_identifier)
            if existing is not None:
                if (
                    existing.payload != event.payload
                    or existing.client_id != event.client_id
                    or existing.event_type != event.event_type
                ):
                    return DeduplicationOutcome(
                        retained_events=(),
                        duplicate_count=duplicate_count,
                        experiment_state=ExperimentState.INVALID,
                    )
                duplicate_count += 1
                continue
            identified[event.unique_identifier] = event
            retained.append(event)
            continue
        identity = (
            event.dataset_name,
            event.client_id,
            event.timestamp_seconds,
            event.event_type,
            event.payload,
        )
        if identity in anonymous:
            duplicate_count += 1
            continue
        anonymous.add(identity)
        retained.append(event)
    return DeduplicationOutcome(
        retained_events=tuple(retained),
        duplicate_count=duplicate_count,
        experiment_state=ExperimentState.READY,
    )


def shannon_entropy(bucket_counts: tuple[RecordCount, ...]) -> FiniteFloat:
    total = sum(bucket_counts)
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in bucket_counts:
        if count <= 0:
            continue
        probability = count / total
        entropy -= probability * log(probability)
    return entropy


def epoch_feature_vector(bucket_counts: tuple[RecordCount, ...]) -> EpochFeatureVector:
    total = sum(bucket_counts)
    log1p_counts = tuple(log1p(count) for count in bucket_counts)
    vector = EpochFeatureVector(
        log1p_bucket_counts=log1p_counts,
        total_raw_event_count=total,
        shannon_entropy=shannon_entropy(bucket_counts),
    )
    if not epoch_features_are_finite(vector):
        raise ValueError("non-finite generated epoch features are a preprocessing failure")
    return vector


def epoch_features_are_finite(vector: EpochFeatureVector) -> Boolean:
    if not isfinite(vector.shannon_entropy):
        return False
    return all(isfinite(count) for count in vector.log1p_bucket_counts)


def empty_epoch_feature_vector(bucket_count: HashBucketCount) -> EpochFeatureVector:
    zeros = tuple(0.0 for _ in range(bucket_count))
    return EpochFeatureVector(
        log1p_bucket_counts=zeros,
        total_raw_event_count=0,
        shannon_entropy=0.0,
    )


def inclusive_epoch_range(
    start_epoch: EpochIndexValue, end_epoch: EpochIndexValue
) -> tuple[EpochIndexValue, ...]:
    if end_epoch < start_epoch:
        return ()
    return tuple(range(start_epoch, end_epoch + 1))


def common_benign_epoch_bounds(
    per_client_epochs: tuple[tuple[EpochIndexValue, ...], ...],
) -> tuple[EpochIndexValue, EpochIndexValue] | None:
    if not per_client_epochs:
        return None
    starts: list[EpochIndexValue] = []
    ends: list[EpochIndexValue] = []
    for epochs in per_client_epochs:
        if not epochs:
            return None
        starts.append(min(epochs))
        ends.append(max(epochs))
    start = max(starts)
    end = min(ends)
    if end < start:
        return None
    return (start, end)


def chronological_benign_partitions(
    epoch_indexes: tuple[EpochIndexValue, ...],
    lengths: ChronologicalPartitionLengths,
) -> ChronologicalBenignPartitions:
    expected = (
        lengths.detector_fit
        + lengths.nuisance_fit
        + lengths.threshold_and_policy_calibration
        + lengths.heldout_benign
    )
    if len(epoch_indexes) != expected:
        raise ValueError("partition lengths must cover the common benign epoch interval")
    detector_end = lengths.detector_fit
    nuisance_end = detector_end + lengths.nuisance_fit
    threshold_end = nuisance_end + lengths.threshold_and_policy_calibration
    return ChronologicalBenignPartitions(
        detector_fit=epoch_indexes[:detector_end],
        nuisance_fit=epoch_indexes[detector_end:nuisance_end],
        threshold_and_policy_calibration=epoch_indexes[nuisance_end:threshold_end],
        heldout_benign=epoch_indexes[threshold_end:],
    )


def fit_robust_scaler(
    detector_fit_values: tuple[FiniteFloat, ...], iqr_floor: NumericalFloor
) -> RobustScaler:
    if not detector_fit_values:
        raise ValueError("robust scaling requires detector_fit values")
    array: NDArray[np.float64] = np.asarray(detector_fit_values, dtype=np.float64)
    if not bool(np.all(np.isfinite(array))):
        raise ValueError("non-finite detector_fit values are a preprocessing failure")
    lower = float(np.quantile(array, 1 / 4))
    upper = float(np.quantile(array, 3 / 4))
    return RobustScaler(
        median=float(np.median(array)),
        iqr=upper - lower,
        iqr_floor=iqr_floor,
    )


def apply_robust_scaler(
    scaler: RobustScaler, values: tuple[FiniteFloat, ...]
) -> tuple[FiniteFloat, ...]:
    denominator = max(scaler.iqr, scaler.iqr_floor)
    scaled: list[FiniteFloat] = []
    for sample in values:
        if not isfinite(sample):
            raise ValueError("non-finite generated features are a preprocessing failure")
        transformed = (sample - scaler.median) / denominator
        if not isfinite(transformed):
            raise ValueError("non-finite generated features are a preprocessing failure")
        scaled.append(transformed)
    return tuple(scaled)


def complete_horizon_count(epoch_count: EpochCount, horizon_length: EpochCount) -> RecordCount:
    if horizon_length <= 0:
        raise ValueError("horizon_length must be positive")
    return epoch_count // horizon_length


def complete_benign_horizons(
    epoch_indexes: tuple[EpochIndexValue, ...], horizon_length: EpochCount
) -> tuple[BenignHorizon, ...]:
    complete = complete_horizon_count(len(epoch_indexes), horizon_length)
    horizons: list[BenignHorizon] = []
    for index in range(complete):
        start = index * horizon_length
        block = epoch_indexes[start : start + horizon_length]
        horizons.append(BenignHorizon(start_epoch=block[0], epoch_indexes=block))
    return tuple(horizons)


def horizon_eligibility_state(
    complete_horizons: RecordCount, required_horizons: RecordCount
) -> ClaimState:
    if complete_horizons < required_horizons:
        return ClaimState.NOT_TESTED
    return ClaimState.SUPPORTED


def detector_fit_sample_requirement_is_met(detector_fit_epoch_count: EpochCount) -> Boolean:
    return detector_fit_epoch_count > 0
