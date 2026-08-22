from fedcampaign_emhi.analysis.claims import claim_identifiers
from fedcampaign_emhi.analysis.multiplicity import (
    holm_adjusted_p_values,
    holm_placeholder_p_value,
    primary_holm_family_identifiers,
)
from fedcampaign_emhi.analysis.statistics import (
    exact_sign_pattern,
    flipped_mean,
    monte_carlo_sign_flip_p_value,
    seed_level_aggregate,
    sign_flip_assignment_count,
    two_sided_sign_flip_p_value,
)
from fedcampaign_emhi.config.loading import load_production_configuration
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
    loaded = load_production_configuration()
    assert len(loaded.values.randomness.real_confirmatory_roots) == 10
    assert sign_flip_assignment_count(10) == 1024
    assert exact_sign_pattern(0, 3) == (1, 1, 1)
    assert exact_sign_pattern(1, 3) == (-1, 1, 1)


def test_seed_level_aggregation_and_two_sided_sign_flip() -> None:
    assert abs(seed_level_aggregate((0.2, 0.4, 0.6)) - 0.4) < 1.0e-12
    differences = (1.0, -0.5)
    observed = flipped_mean(differences, (1, 1))
    flipped = (flipped_mean(differences, exact_sign_pattern(index, 2)) for index in range(4))
    p_value = two_sided_sign_flip_p_value(observed, tuple(flipped))
    assert 0.0 <= p_value <= 1.0
    assert monte_carlo_sign_flip_p_value(3, 99) == 4 / 100
