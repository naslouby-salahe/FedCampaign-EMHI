from dataclasses import dataclass

from fedcampaign_emhi.domain.types import (
    EpochIndexValue,
    EpochSeconds,
    FiniteFloat,
    PositiveEpochCount,
)


@dataclass(frozen=True)
class CampaignReplayPlan:
    warmup_epochs: tuple[EpochIndexValue, ...]
    campaign_epochs: tuple[EpochIndexValue, ...]
    global_state_reset: bool
    local_persistence_reset: bool


def campaign_replay_plan(
    campaign_start_epoch: EpochIndexValue,
    prestart_warmup_epochs: PositiveEpochCount,
    evaluation_horizon_epochs: PositiveEpochCount,
) -> CampaignReplayPlan:
    if prestart_warmup_epochs <= 0 or evaluation_horizon_epochs <= 0:
        raise ValueError("warm-up and horizon must be positive")
    warmup = tuple(range(campaign_start_epoch - prestart_warmup_epochs, campaign_start_epoch))
    campaign = tuple(range(campaign_start_epoch, campaign_start_epoch + evaluation_horizon_epochs))
    return CampaignReplayPlan(
        warmup_epochs=warmup,
        campaign_epochs=campaign,
        global_state_reset=True,
        local_persistence_reset=True,
    )


def statistical_lead(
    earliest_local_stop_epoch: EpochIndexValue, global_stop_epoch: EpochIndexValue
) -> FiniteFloat:
    return earliest_local_stop_epoch - global_stop_epoch


def operational_lead(
    earliest_local_stop_epoch: EpochIndexValue,
    global_stop_epoch: EpochIndexValue,
    detection_delay_seconds: FiniteFloat,
    real_data_epoch_seconds: EpochSeconds,
) -> FiniteFloat:
    delay_in_epochs = detection_delay_seconds / real_data_epoch_seconds
    return earliest_local_stop_epoch - (global_stop_epoch + delay_in_epochs)
