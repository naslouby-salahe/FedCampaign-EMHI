from fedcampaign_emhi.analysis.claims import claim_identifiers, evaluate_threshold_claim
from fedcampaign_emhi.domain.enums import ClaimIdentifier, ClaimState
from fedcampaign_emhi.emhi.thresholds import operating_point_unavailable_outcome


def test_operating_point_unavailable_is_not_an_implementation_error() -> None:
    outcome = operating_point_unavailable_outcome()
    assert outcome.is_implementation_error is False
    assert claim_identifiers()


def test_strict_odi_claim_requires_operating_point_and_materiality() -> None:
    supported = evaluate_threshold_claim(ClaimIdentifier.CLAIM_STRICT_ODI, 0.3, 0.2, True)
    unsupported = evaluate_threshold_claim(ClaimIdentifier.CLAIM_STRICT_ODI, 0.1, 0.2, True)
    untested = evaluate_threshold_claim(ClaimIdentifier.CLAIM_STRICT_ODI, 0.9, 0.2, False)
    assert supported.state is ClaimState.SUPPORTED
    assert unsupported.state is ClaimState.NOT_SUPPORTED
    assert untested.state is ClaimState.NOT_TESTED
