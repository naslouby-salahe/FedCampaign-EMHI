import numpy as np
from scipy.stats import beta

from fedcampaign_emhi.domain.enums import OperatingPointState
from fedcampaign_emhi.domain.types import (
    ConfidenceLevel,
    EpochCount,
    EpochIndexValue,
    FalseAlarmRate,
    FiniteFloat,
    LocalPolicyArtifact,
    PositiveInt,
    Probability,
    Quantile,
    RecordCount,
    ThresholdValue,
)


def persistence_is_triggered(
    exceedances: tuple[bool, ...],
    required_exceedances: PositiveInt,
    window_epochs: EpochCount,
) -> bool:
    if window_epochs <= 0:
        raise ValueError("window_epochs must be positive")
    examined = exceedances[-window_epochs:]
    if len(examined) < required_exceedances:
        return False
    return sum(1 for exceeded in examined if exceeded) >= required_exceedances


def score_exceeds_threshold(score: FiniteFloat, threshold: FiniteFloat) -> bool:
    return score >= threshold


def first_local_stop_epoch(
    exceedances: tuple[bool, ...],
    required_exceedances: PositiveInt,
    window_epochs: EpochCount,
) -> EpochIndexValue | None:
    for end_index in range(1, len(exceedances) + 1):
        if persistence_is_triggered(exceedances[:end_index], required_exceedances, window_epochs):
            return end_index - 1
    return None


def candidate_thresholds_from_nuisance_scores(
    nuisance_scores: tuple[FiniteFloat, ...],
    quantiles: tuple[Quantile, ...],
) -> tuple[ThresholdValue, ...]:
    if not nuisance_scores:
        raise ValueError("nuisance_fit scores are required for candidate thresholds")
    array = np.asarray(nuisance_scores, dtype=np.float64)
    return tuple(float(np.quantile(array, quantile)) for quantile in quantiles)


def local_policy_clopper_pearson_upper_bound(
    false_stop_count: RecordCount,
    horizon_count: RecordCount,
    confidence: ConfidenceLevel,
) -> Probability:
    if horizon_count <= 0:
        raise ValueError("horizon_count must be positive")
    if false_stop_count < 0 or false_stop_count > horizon_count:
        raise ValueError("false_stop_count must lie in [0, horizon_count]")
    if false_stop_count == horizon_count:
        return 1.0
    return float(beta.ppf(confidence, false_stop_count + 1, horizon_count - false_stop_count))


def select_immutable_local_policy(
    candidates: tuple[LocalPolicyArtifact, ...],
    calibration_false_stop_counts: tuple[RecordCount, ...],
    horizon_count: RecordCount,
    confidence: ConfidenceLevel,
    target_pfa: FalseAlarmRate,
) -> LocalPolicyArtifact | None:
    if len(candidates) != len(calibration_false_stop_counts):
        raise ValueError("candidates and calibration_false_stop_counts must have equal length")
    ordered = sorted(
        zip(candidates, calibration_false_stop_counts, strict=True),
        key=lambda pair: (pair[0].threshold, pair[0].required_exceedances, pair[0].window_epochs),
    )
    for artifact, false_stop_count in ordered:
        upper = local_policy_clopper_pearson_upper_bound(
            false_stop_count, horizon_count, confidence
        )
        if upper <= target_pfa:
            return artifact
    return None


def heldout_false_stop_count(
    heldout_exceedance_horizons: tuple[tuple[bool, ...], ...],
    required_exceedances: PositiveInt,
    window_epochs: EpochCount,
) -> RecordCount:
    stops = 0
    for horizon in heldout_exceedance_horizons:
        if first_local_stop_epoch(horizon, required_exceedances, window_epochs) is not None:
            stops += 1
    return stops


def operating_point_state_for_policy(
    artifact: LocalPolicyArtifact | None,
) -> OperatingPointState:
    if artifact is None:
        return OperatingPointState.UNAVAILABLE
    return OperatingPointState.AVAILABLE
