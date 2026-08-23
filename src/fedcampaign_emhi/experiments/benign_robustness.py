from dataclasses import dataclass

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import DatasetName, MethodName
from fedcampaign_emhi.domain.types import (
    EpochCount,
    FiniteFloat,
    Probability,
    RecordCount,
    SeedCount,
)


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


def select_top_event_count_windows(
    window_event_counts: tuple[RecordCount, ...], fraction: Probability
) -> tuple[RecordCount, ...]:
    if not 0.0 < fraction <= 1.0:
        raise ValueError("top event-count fraction must lie in (0, 1]")
    if not window_event_counts:
        raise ValueError("window selection requires at least one candidate window")
    ranked = sorted(window_event_counts, reverse=True)
    target = fraction * len(ranked)
    selected = int(target)
    threshold = ranked[selected - 1] if selected > 0 else ranked[-1]
    kept = [count for count in ranked if count >= threshold]
    return tuple(kept)


def synthetic_count_stress_multiplier(
    bucket_counts: tuple[RecordCount, ...], factor: FiniteFloat
) -> tuple[FiniteFloat, ...]:
    if factor <= 0.0:
        raise ValueError("benign count multiplication factors must be positive")
    if not bucket_counts:
        raise ValueError("count stress requires at least one raw event-count bucket")
    return tuple(float(count) * factor for count in bucket_counts)


def false_campaign_suppression_gate(
    mean_suppression: Probability, minimum_suppression: Probability
) -> bool:
    return mean_suppression >= minimum_suppression


def power_loss_gate(mean_loss: FiniteFloat, maximum_loss: Probability) -> bool:
    return mean_loss <= maximum_loss


def seed_level_power_loss(
    no_outside_detection_rate: Probability, emhi_detection_rate: Probability
) -> FiniteFloat:
    return no_outside_detection_rate - emhi_detection_rate


def paired_false_campaign_difference(
    raw_mean_fcr: Probability, emhi_fcr: Probability
) -> FiniteFloat:
    return raw_mean_fcr - emhi_fcr
