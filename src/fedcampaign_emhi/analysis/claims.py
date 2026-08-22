from fedcampaign_emhi.domain.enums import ClaimIdentifier, ClaimState
from fedcampaign_emhi.domain.types import ClaimEvaluation, Probability


def claim_identifiers() -> tuple[ClaimIdentifier, ...]:
    return tuple(ClaimIdentifier)


def evaluate_threshold_claim(
    identifier: ClaimIdentifier,
    observed: Probability | None,
    minimum: Probability,
    operating_point_available: bool,
) -> ClaimEvaluation:
    if not operating_point_available or observed is None:
        return ClaimEvaluation(identifier=identifier, state=ClaimState.NOT_TESTED)
    if observed >= minimum:
        return ClaimEvaluation(identifier=identifier, state=ClaimState.SUPPORTED)
    return ClaimEvaluation(identifier=identifier, state=ClaimState.NOT_SUPPORTED)
