from fedcampaign_emhi.domain.types import ResumeStep
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE


def recovery_sequence() -> tuple[ResumeStep, ...]:
    return RESUME_SEQUENCE
