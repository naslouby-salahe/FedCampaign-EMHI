from scipy.stats import beta

from fedcampaign_emhi.domain.types import (
    ConfidenceLevel,
    ESrThreshold,
    FalseAlarmRate,
    Probability,
    RecordCount,
    ThresholdValue,
)


def clopper_pearson_one_sided_upper_bound(
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
    upper = float(beta.ppf(confidence, false_stop_count + 1, horizon_count - false_stop_count))
    return upper


def select_calibrated_threshold(
    candidates: tuple[ThresholdValue, ...],
    false_stop_counts: tuple[RecordCount, ...],
    horizon_count: RecordCount,
    confidence: ConfidenceLevel,
    target_pfa: FalseAlarmRate,
) -> ThresholdValue | None:
    if len(candidates) != len(false_stop_counts):
        raise ValueError("candidates and false_stop_counts must have equal length")
    ordered = sorted(zip(candidates, false_stop_counts, strict=True), key=lambda pair: pair[0])
    for threshold, false_stop_count in ordered:
        upper = clopper_pearson_one_sided_upper_bound(false_stop_count, horizon_count, confidence)
        if upper <= target_pfa:
            return threshold
    return None


def esr_threshold_from_arl_alpha(arl_alpha: FalseAlarmRate) -> ESrThreshold:
    return 1.0 / arl_alpha
