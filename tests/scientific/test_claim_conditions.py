from fedcampaign_emhi.analysis.claims import claim_identifiers
from fedcampaign_emhi.emhi.thresholds import operating_point_unavailable_outcome


def test_operating_point_unavailable_is_not_an_implementation_error() -> None:
    outcome = operating_point_unavailable_outcome()
    assert outcome.is_implementation_error is False
    assert claim_identifiers()
