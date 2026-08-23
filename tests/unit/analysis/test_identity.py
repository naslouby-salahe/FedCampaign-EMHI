import pytest

from fedcampaign_emhi.analysis.identity import (
    CONTRIBUTION_IDENTITY,
    NOT_NOVEL_COMPONENTS,
    ContributionIdentity,
    all_declared_components_have_explicit_novelty_scope,
    contribution_identity_matches,
    no_novelty_claim_outside_identity,
    roadmap_is_scientific_authority,
)


def test_contribution_identity_is_byte_exact() -> None:
    assert CONTRIBUTION_IDENTITY.name == (
        "FedCampaign-EMHI — Exclusion-Matched Hierarchical Innovation"
    )
    assert CONTRIBUTION_IDENTITY.research_object == ("Operational Distributed Insufficiency (ODI)")
    assert CONTRIBUTION_IDENTITY.theoretical_principle == (
        "Exclusion-Matched Irreducible Innovation (EMII)"
    )


def test_identity_match_detects_any_drift() -> None:
    assert contribution_identity_matches(CONTRIBUTION_IDENTITY, CONTRIBUTION_IDENTITY) is True
    drifted = ContributionIdentity(
        name="FedCampaign-EMHI — Exclusion-Matched Hierarchical Innovation v2",
        research_object=CONTRIBUTION_IDENTITY.research_object,
        theoretical_principle=CONTRIBUTION_IDENTITY.theoretical_principle,
    )
    assert contribution_identity_matches(drifted, CONTRIBUTION_IDENTITY) is False


def test_every_declared_component_disclaims_novelty() -> None:
    for boundary in NOT_NOVEL_COMPONENTS:
        assert boundary.novelty_claimed is False


def test_no_novelty_claim_enforced_for_declared_components() -> None:
    for boundary in NOT_NOVEL_COMPONENTS:
        assert no_novelty_claim_outside_identity(boundary.component) is True


def test_unknown_component_fails_loudly() -> None:
    with pytest.raises(ValueError):
        no_novelty_claim_outside_identity("quantum annealing")


def test_roadmap_authority_and_scope_completeness() -> None:
    assert roadmap_is_scientific_authority() is True
    assert all_declared_components_have_explicit_novelty_scope() is True
