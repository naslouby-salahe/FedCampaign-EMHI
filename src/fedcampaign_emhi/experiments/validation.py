import statistics
from dataclasses import dataclass

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import DatasetName, ExperimentName, MethodName
from fedcampaign_emhi.domain.types import (
    Boolean,
    ClientCount,
    ClientId,
    ComponentName,
    EpochCount,
    FiniteFloat,
    Probability,
    RecordCount,
    SeedCount,
)
from fedcampaign_emhi.experiments.definitions import experiment_registry

PRIMARY_CAUSAL_COMPARATOR = MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI


@dataclass(frozen=True)
class PrimaryStrictOdiPlan:
    dataset_name: DatasetName
    methods: tuple[MethodName, ...]
    development_seed_count: SeedCount
    confirmatory_seed_count: SeedCount
    minimum_strict_odi_rate: Probability
    minimum_odi_advantage: Probability
    minimum_median_operational_lead_epochs: FiniteFloat


@dataclass(frozen=True)
class FullMethodSupportInputs:
    heldout_pfa_upper_bound: Probability
    target_pfa: Probability
    mean_strict_odi_rate: Probability
    minimum_strict_odi_rate: Probability
    paired_odi_advantage: FiniteFloat
    minimum_odi_advantage: Probability
    median_lead_among_successes: FiniteFloat
    minimum_median_lead: FiniteFloat
    directional_adjusted_p_value: Probability
    nominal_alpha: Probability
    full_operating_point_available: Boolean
    comparator_operating_point_available: Boolean


@dataclass(frozen=True)
class FullMethodSupportResult:
    pfa_gate_passes: Boolean
    odi_rate_gate_passes: Boolean
    advantage_gate_passes: Boolean
    lead_gate_passes: Boolean
    directional_gate_passes: Boolean
    matched_operating_point_gate_passes: Boolean

    @property
    def all_criteria_pass(self) -> Boolean:
        return (
            self.pfa_gate_passes
            and self.odi_rate_gate_passes
            and self.advantage_gate_passes
            and self.lead_gate_passes
            and self.directional_gate_passes
            and self.matched_operating_point_gate_passes
        )

    @property
    def failed_criteria(self) -> tuple[ComponentName, ...]:
        checks = (
            ("heldout_pfa", self.pfa_gate_passes),
            ("strict_odi_rate", self.odi_rate_gate_passes),
            ("paired_odi_advantage", self.advantage_gate_passes),
            ("median_operational_lead", self.lead_gate_passes),
            ("directional_inference", self.directional_gate_passes),
            ("matched_operating_point", self.matched_operating_point_gate_passes),
        )
        return tuple(name for name, passed in checks if not passed)


def assert_known_experiment(config: ScientificConfig, experiment_name: ExperimentName) -> None:
    names = {contract.experiment_name for contract in experiment_registry(config)}
    if experiment_name not in names:
        raise ValueError(f"experiment {experiment_name.value} is not in the configured registry")


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


def strict_odi_rate_gate(mean_odi_rate: Probability, minimum_rate: Probability) -> Boolean:
    return mean_odi_rate >= minimum_rate


def paired_odi_advantage_gate(
    full_odi_rate: Probability,
    comparator_odi_rate: Probability,
    minimum_advantage: Probability,
) -> Boolean:
    return (full_odi_rate - comparator_odi_rate) >= minimum_advantage


def median_operational_lead_gate(
    median_lead_epochs: FiniteFloat,
    minimum_lead_epochs: FiniteFloat,
) -> Boolean:
    return median_lead_epochs >= minimum_lead_epochs


def median_of(values: tuple[FiniteFloat, ...]) -> FiniteFloat:
    if not values:
        raise ValueError("median requires at least one value")
    return statistics.median(values)


def matched_operating_point_requirement(
    full_method_available: Boolean,
    comparator_available: Boolean,
) -> Boolean:
    return full_method_available and comparator_available


def campaign_evaluation_universe(registry_size: RecordCount) -> RecordCount:
    if registry_size <= 0:
        raise ValueError("campaign evaluation requires at least one eligible campaign")
    return registry_size


def campaign_registry_universe_size(
    participating_clients: tuple[tuple[ClientId, ...], ...],
    minimum_clients: ClientCount,
) -> RecordCount:
    eligible = sum(1 for clients in participating_clients if len(clients) >= minimum_clients)
    universe: RecordCount = eligible
    return universe


def evaluation_epoch_budget(
    campaign_count: RecordCount,
    horizon_epochs: EpochCount,
) -> RecordCount:
    if horizon_epochs <= 0:
        raise ValueError("evaluation horizon must be positive")
    budget: RecordCount = campaign_count * horizon_epochs
    return budget


def evaluate_full_method_support(inputs: FullMethodSupportInputs) -> FullMethodSupportResult:
    return FullMethodSupportResult(
        pfa_gate_passes=inputs.heldout_pfa_upper_bound <= inputs.target_pfa,
        odi_rate_gate_passes=strict_odi_rate_gate(
            inputs.mean_strict_odi_rate,
            inputs.minimum_strict_odi_rate,
        ),
        advantage_gate_passes=paired_odi_advantage_gate(
            inputs.paired_odi_advantage,
            0.0,
            inputs.minimum_odi_advantage,
        ),
        lead_gate_passes=median_operational_lead_gate(
            inputs.median_lead_among_successes,
            inputs.minimum_median_lead,
        ),
        directional_gate_passes=inputs.directional_adjusted_p_value < inputs.nominal_alpha,
        matched_operating_point_gate_passes=matched_operating_point_requirement(
            inputs.full_operating_point_available,
            inputs.comparator_operating_point_available,
        ),
    )
