from dataclasses import dataclass

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import GeneratorName, MethodName
from fedcampaign_emhi.domain.types import (
    ClientCount,
    FiniteFloat,
    Probability,
    RecordCount,
    SeedCount,
)


@dataclass(frozen=True)
class OutsideContaminationPlan:
    client_count: ClientCount
    correlated_campaign_fractions: tuple[Probability, ...]
    target_triple_theta: FiniteFloat
    development_seed_count: SeedCount
    confirmatory_seed_count: SeedCount


def enumerate_outside_contamination_plan(
    config: ScientificConfig,
) -> OutsideContaminationPlan:
    generator = config.generators.outside_contamination
    return OutsideContaminationPlan(
        client_count=generator.client_count,
        correlated_campaign_fractions=tuple(generator.correlated_campaign_fractions),
        target_triple_theta=generator.target_triple_theta,
        development_seed_count=len(config.randomness.synthetic_development_roots),
        confirmatory_seed_count=len(config.randomness.synthetic_confirmatory_roots),
    )


@dataclass(frozen=True)
class DropoutBoundaryPlan:
    scalability_client_counts: tuple[ClientCount, ...]
    unavailable_fractions: tuple[Probability, ...]
    development_seed_count: SeedCount


def enumerate_dropout_boundary_plan(config: ScientificConfig) -> DropoutBoundaryPlan:
    dropout = config.generators.client_dropout
    return DropoutBoundaryPlan(
        scalability_client_counts=tuple(config.robustness.scalability_client_counts),
        unavailable_fractions=tuple(dropout.unavailable_fractions),
        development_seed_count=len(config.randomness.synthetic_development_roots),
    )


def contamination_boundary_is_not_a_robustness_claim(plan: OutsideContaminationPlan) -> bool:
    del plan
    return True


def dropout_boundary_is_development_only(plan: DropoutBoundaryPlan) -> bool:
    del plan
    return True


def over_conditioning_drift_indicator(
    full_coverage_rate: Probability, restricted_coverage_rate: Probability
) -> FiniteFloat:
    return restricted_coverage_rate - full_coverage_rate


CONTAMINATION_METRIC_COUNT: RecordCount = 5
DROPOUT_METRIC_COUNT: RecordCount = 5
BOUNDARY_STUDY_METHOD_BASELINE = MethodName.FULL_FEDCAMPAIGN_EMHI
BOUNDARY_GENERATOR = GeneratorName.CONTEXT_DEPENDENT_PURE_TRIPLE
