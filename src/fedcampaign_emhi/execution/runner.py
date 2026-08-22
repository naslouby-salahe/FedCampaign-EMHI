from fedcampaign_emhi.domain.enums import ExperimentName, ExperimentState
from fedcampaign_emhi.domain.types import ResumeStep
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE


def resume_sequence() -> tuple[ResumeStep, ...]:
    return RESUME_SEQUENCE


def run_is_blocked_until_scientific_producers_exist(
    experiment_name: ExperimentName,
) -> ExperimentState:
    return ExperimentState.READY if experiment_name else ExperimentState.BLOCKED
