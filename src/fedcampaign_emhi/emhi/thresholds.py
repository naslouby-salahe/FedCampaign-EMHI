from fedcampaign_emhi.domain.enums import (
    ExperimentState,
    OperatingPointState,
    ScientificOutcomeKind,
)
from fedcampaign_emhi.domain.types import ScientificOutcome


def operating_point_unavailable_outcome() -> ScientificOutcome:
    return ScientificOutcome(
        kind=ScientificOutcomeKind.OPERATING_POINT_UNAVAILABLE,
        operating_point_state=OperatingPointState.UNAVAILABLE,
        experiment_state=ExperimentState.COMPLETED,
        is_implementation_error=False,
    )


def unfavorable_completed_outcome() -> ScientificOutcome:
    return ScientificOutcome(
        kind=ScientificOutcomeKind.COMPLETED_UNFAVORABLE,
        operating_point_state=OperatingPointState.AVAILABLE,
        experiment_state=ExperimentState.COMPLETED,
        is_implementation_error=False,
    )
