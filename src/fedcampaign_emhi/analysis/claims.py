from fedcampaign_emhi.domain.enums import ClaimIdentifier


def claim_identifiers() -> tuple[ClaimIdentifier, ...]:
    return tuple(ClaimIdentifier)
