from dataclasses import dataclass

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import DatasetName, MethodName
from fedcampaign_emhi.domain.types import (
    ClientCount,
    ClientId,
    EpochCount,
    FiniteFloat,
    Probability,
    RecordCount,
    SeedCount,
)


@dataclass(frozen=True)
class PrimaryStrictOdiPlan:
    dataset_name: DatasetName
    methods: tuple[MethodName, ...]
    development_seed_count: SeedCount
    confirmatory_seed_count: SeedCount
    minimum_strict_odi_rate: Probability
    minimum_odi_advantage: Probability
    minimum_median_operational_lead_epochs: FiniteFloat


def enumerate_primary_strict_odi_plan(config: ScientificConfig) -> PrimaryStrictOdiPlan:
    experiment = config.experiments.primary_strict_odi_evaluation
    materiality = config.claim_materiality.primary_real
    return PrimaryStrictOdiPlan(
        dataset_name=config.datasets.primary.name,
        methods=tuple(experiment.methods),
        development_seed_count=len(config.randomness.real_development_roots),
        confirmatory_seed_count=len(config.randomness.real_confirmatory_roots),
        minimum_strict_odi_rate=materiality.minimum_strict_odi_rate,
        minimum_odi_advantage=materiality.minimum_odi_rate_advantage_over_order_at_most_two,
        minimum_median_operational_lead_epochs=materiality.minimum_median_operational_lead_epochs,
    )


PRIMARY_CAUSAL_COMPARATOR = MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI


def strict_odi_rate_gate(mean_odi_rate: Probability, minimum_rate: Probability) -> bool:
    return mean_odi_rate >= minimum_rate


def paired_odi_advantage_gate(
    full_odi_rate: Probability, comparator_odi_rate: Probability, minimum_advantage: Probability
) -> bool:
    return (full_odi_rate - comparator_odi_rate) >= minimum_advantage


def median_operational_lead_gate(
    median_lead_epochs: FiniteFloat, minimum_lead_epochs: FiniteFloat
) -> bool:
    return median_lead_epochs >= minimum_lead_epochs


def median_of(values: tuple[FiniteFloat, ...]) -> FiniteFloat:
    if not values:
        raise ValueError("median requires at least one value")
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def matched_operating_point_requirement(
    full_method_available: bool, comparator_available: bool
) -> bool:
    return full_method_available and comparator_available


def campaign_evaluation_universe(registry_size: RecordCount) -> RecordCount:
    if registry_size <= 0:
        raise ValueError("campaign evaluation requires at least one eligible campaign")
    return registry_size


def campaign_registry_universe_size(
    participating_clients: tuple[tuple[ClientId, ...], ...], minimum_clients: ClientCount
) -> RecordCount:
    eligible = sum(1 for clients in participating_clients if len(clients) >= minimum_clients)
    universe: RecordCount = eligible
    return universe


def evaluation_epoch_budget(campaign_count: RecordCount, horizon_epochs: EpochCount) -> RecordCount:
    if horizon_epochs <= 0:
        raise ValueError("evaluation horizon must be positive")
    budget: RecordCount = campaign_count * horizon_epochs
    return budget
