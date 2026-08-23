from dataclasses import dataclass

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import DatasetName, MethodName
from fedcampaign_emhi.domain.types import (
    FiniteFloat,
    Probability,
    SeedCount,
)


@dataclass(frozen=True)
class StrongLocalPolicyPlan:
    dataset_name: DatasetName
    global_method: MethodName
    development_seed_count: SeedCount
    confirmatory_seed_count: SeedCount
    minimum_strict_odi_rate: Probability


def enumerate_strong_local_policy_plan(config: ScientificConfig) -> StrongLocalPolicyPlan:
    materiality = config.claim_materiality.strong_local
    return StrongLocalPolicyPlan(
        dataset_name=config.datasets.primary.name,
        global_method=MethodName.FULL_FEDCAMPAIGN_EMHI,
        development_seed_count=len(config.randomness.real_development_roots),
        confirmatory_seed_count=len(config.randomness.real_confirmatory_roots),
        minimum_strict_odi_rate=materiality.minimum_strict_odi_rate,
    )


def strong_local_odi_rate_gate(
    mean_odi_rate: Probability, minimum_strict_odi_rate: Probability
) -> bool:
    return mean_odi_rate >= minimum_strict_odi_rate


def strong_local_directional_margin(
    seed_odi_rates: tuple[Probability, ...], minimum_strict_odi_rate: Probability
) -> FiniteFloat:
    if not seed_odi_rates:
        raise ValueError("directional margin requires at least one seed")
    return sum(seed_odi_rates) / len(seed_odi_rates) - minimum_strict_odi_rate
