from dataclasses import dataclass

from fedcampaign_emhi.domain.types import ComponentName


@dataclass(frozen=True)
class ContributionIdentity:
    name: ComponentName
    research_object: ComponentName
    theoretical_principle: ComponentName


CONTRIBUTION_IDENTITY = ContributionIdentity(
    name="FedCampaign-EMHI — Exclusion-Matched Hierarchical Innovation",
    research_object="Operational Distributed Insufficiency (ODI)",
    theoretical_principle="Exclusion-Matched Irreducible Innovation (EMII)",
)


@dataclass(frozen=True)
class NoveltyBoundary:
    component: ComponentName
    novelty_claimed: bool


NOT_NOVEL_COMPONENTS: tuple[NoveltyBoundary, ...] = (
    NoveltyBoundary("Hoeffding", False),
    NoveltyBoundary("functional ANOVA decomposition", False),
    NoveltyBoundary("hierarchical orthogonal functional decomposition", False),
    NoveltyBoundary("Hilbert-space projection", False),
    NoveltyBoundary("empirical ranks", False),
    NoveltyBoundary("conditional predictive information", False),
    NoveltyBoundary("copulas", False),
    NoveltyBoundary("Lancaster/Streitberg interactions", False),
    NoveltyBoundary("connected information", False),
    NoveltyBoundary("vine decompositions", False),
)


def roadmap_is_scientific_authority() -> bool:
    return True


def contribution_identity_matches(
    observed: ContributionIdentity, authoritative: ContributionIdentity
) -> bool:
    return (
        observed.name == authoritative.name
        and observed.research_object == authoritative.research_object
        and observed.theoretical_principle == authoritative.theoretical_principle
    )


def no_novelty_claim_outside_identity(component: ComponentName) -> bool:
    for boundary in NOT_NOVEL_COMPONENTS:
        if boundary.component == component:
            return not boundary.novelty_claimed
    raise ValueError(f"unknown novelty-boundary component: {component}")


def all_declared_components_have_explicit_novelty_scope() -> bool:
    return len(NOT_NOVEL_COMPONENTS) > 0
