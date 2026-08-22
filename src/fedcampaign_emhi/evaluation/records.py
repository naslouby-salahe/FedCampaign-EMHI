from fedcampaign_emhi.domain.types import EpochIndexValue, StrictOdiOutcome
from fedcampaign_emhi.evaluation.metrics import strict_odi_outcome


def odi_evaluation_record(
    global_stop_epoch: EpochIndexValue | None,
    local_stop_epochs: tuple[EpochIndexValue | None, ...],
) -> StrictOdiOutcome:
    return strict_odi_outcome(global_stop_epoch, local_stop_epochs)


def global_detection_without_odi(outcome: StrictOdiOutcome) -> bool:
    return outcome.global_detection_indicator == 1 and outcome.indicator == 0
