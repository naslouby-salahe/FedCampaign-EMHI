from fedcampaign_emhi.analysis.claims import claim_identifiers
from fedcampaign_emhi.analysis.multiplicity import (
    holm_adjusted_p_values,
    holm_placeholder_p_value,
    primary_holm_family_identifiers,
)
from fedcampaign_emhi.analysis.statistics import exact_sign_pattern, sign_flip_assignment_count
from fedcampaign_emhi.domain.enums import ClaimIdentifier


def test_claim_identifiers_are_complete() -> None:
    assert ClaimIdentifier.CLAIM_STRICT_ODI in claim_identifiers()


def test_holm_family_has_five_primary_hypotheses() -> None:
    identifiers = primary_holm_family_identifiers()
    assert len(identifiers) == 5
    adjusted = holm_adjusted_p_values(identifiers, (0.01, 0.04, 0.03, 0.20, 0.50))
    assert adjusted[0] <= 0.05
    assert holm_placeholder_p_value() == 1.0


def test_exact_sign_flip_family_for_ten_seeds() -> None:
    assert sign_flip_assignment_count(10) == 1024
    assert exact_sign_pattern(0, 3) == (1, 1, 1)
    assert exact_sign_pattern(1, 3) == (-1, 1, 1)
