from dataclasses import dataclass
from itertools import groupby
from math import expm1, log1p

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.datasets.preprocessing import shannon_entropy
from fedcampaign_emhi.domain.enums import DatasetName, MethodName
from fedcampaign_emhi.domain.types import (
    BenignHorizon,
    Boolean,
    ClientId,
    DetectionRateLoss,
    EpochCount,
    EpochIndexValue,
    FeatureValue,
    Probability,
    RecordCount,
    RobustnessCountMultiplier,
    SeedCount,
    StressBucketCount,
)


@dataclass(frozen=True)
class EpochEventVolume:
    client_id: ClientId
    epoch_index: EpochIndexValue
    raw_event_count: RecordCount


@dataclass(frozen=True)
class BenignCommonModePlan:
    dataset_name: DatasetName
    methods: tuple[MethodName, ...]
    development_seed_count: SeedCount
    confirmatory_seed_count: SeedCount
    stress_stride_epochs: EpochCount
    top_event_count_fraction: Probability


def enumerate_benign_common_mode_plan(config: ScientificConfig) -> BenignCommonModePlan:
    robustness = config.experiments.benign_common_mode_robustness
    return BenignCommonModePlan(
        dataset_name=config.datasets.primary.name,
        methods=tuple(robustness.methods),
        development_seed_count=len(config.randomness.real_development_roots),
        confirmatory_seed_count=len(config.randomness.real_confirmatory_roots),
        stress_stride_epochs=robustness.native_high_volume_window.stride_epochs,
        top_event_count_fraction=robustness.native_high_volume_window.top_event_count_fraction,
    )


def _top_event_count_threshold(
    window_event_counts: tuple[RecordCount, ...], fraction: Probability
) -> RecordCount:
    if not 0.0 < fraction <= 1.0:
        raise ValueError("top event-count fraction must lie in (0, 1]")
    if not window_event_counts:
        raise ValueError("window selection requires at least one candidate window")
    ranked = sorted(window_event_counts, reverse=True)
    target = fraction * len(ranked)
    selected = int(target)
    return ranked[selected - 1] if selected > 0 else ranked[-1]


def rolling_benign_horizons(
    epoch_indexes: tuple[EpochIndexValue, ...],
    horizon_length: EpochCount,
    stride: EpochCount,
) -> tuple[BenignHorizon, ...]:
    if horizon_length <= 0:
        raise ValueError("rolling horizons require a positive horizon length")
    if stride <= 0:
        raise ValueError("rolling horizons require a positive stride")
    horizons: list[BenignHorizon] = []
    start = 0
    while start + horizon_length <= len(epoch_indexes):
        block = epoch_indexes[start : start + horizon_length]
        horizons.append(BenignHorizon(start_epoch=block[0], epoch_indexes=block))
        start += stride
    return tuple(horizons)


def federation_wide_epoch_event_counts(
    epochs: tuple[EpochEventVolume, ...],
    selected_client_ids: tuple[ClientId, ...],
) -> tuple[tuple[EpochIndexValue, RecordCount], ...]:
    selected = set(selected_client_ids)
    relevant = sorted(
        (epoch.epoch_index, epoch.raw_event_count)
        for epoch in epochs
        if epoch.client_id in selected
    )
    totals: list[tuple[EpochIndexValue, RecordCount]] = []
    for epoch_index, group in groupby(relevant, key=lambda item: item[0]):
        totals.append((epoch_index, sum(count for _index, count in group)))
    return tuple(totals)


def window_event_counts(
    windows: tuple[BenignHorizon, ...],
    epoch_event_counts: tuple[tuple[EpochIndexValue, RecordCount], ...],
) -> tuple[RecordCount, ...]:
    totals = dict(epoch_event_counts)
    return tuple(sum(totals.get(epoch, 0) for epoch in window.epoch_indexes) for window in windows)


def select_high_volume_windows(
    windows: tuple[BenignHorizon, ...],
    counts: tuple[RecordCount, ...],
    fraction: Probability,
) -> tuple[BenignHorizon, ...]:
    if len(windows) != len(counts):
        raise ValueError("windows and counts must have equal length")
    threshold = _top_event_count_threshold(counts, fraction)
    return tuple(
        window for window, count in zip(windows, counts, strict=True) if count >= threshold
    )


def paired_false_campaign_difference(
    raw_mean_fcr: Probability, emhi_fcr: Probability
) -> DetectionRateLoss:
    return raw_mean_fcr - emhi_fcr


def synthetic_count_stress_multiplier(
    bucket_counts: tuple[StressBucketCount, ...], factor: RobustnessCountMultiplier
) -> tuple[StressBucketCount, ...]:
    if factor <= 0.0:
        raise ValueError("benign count multiplication factors must be positive")
    if not bucket_counts:
        raise ValueError("count stress requires at least one raw event-count bucket")
    return tuple(count * factor for count in bucket_counts)


def false_campaign_suppression_meets_minimum(
    mean_suppression: Probability, minimum_suppression: Probability
) -> Boolean:
    return mean_suppression >= minimum_suppression


def detection_rate_loss_within_maximum(
    mean_loss: DetectionRateLoss, maximum_loss: DetectionRateLoss
) -> Boolean:
    return mean_loss <= maximum_loss


def stress_epoch_feature_values(
    unscaled_feature_values: tuple[FeatureValue, ...],
    factor: RobustnessCountMultiplier,
) -> tuple[FeatureValue, ...]:
    if len(unscaled_feature_values) < 2:
        raise ValueError(
            "count stress requires at least one bucket plus the total/entropy dimensions"
        )
    bucket_values = unscaled_feature_values[:-2]
    total_value = unscaled_feature_values[-2]
    bucket_counts = tuple(expm1(value) for value in bucket_values)
    stressed_counts = synthetic_count_stress_multiplier(bucket_counts, factor)
    stressed_log1p = tuple(log1p(count) for count in stressed_counts)
    return (*stressed_log1p, total_value * factor, shannon_entropy(stressed_counts))
