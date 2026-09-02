import statistics
from dataclasses import dataclass

from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, MethodName
from fedcampaign_emhi.domain.types import (
    ArtifactFilename,
    Boolean,
    OdiRateAdvantage,
    OperationalLeadEpochs,
    Probability,
    SeedCount,
    SeedValue,
)


@dataclass(frozen=True)
class ExperimentContract:
    experiment_name: ExperimentName
    execution_roles: tuple[ExecutionRole, ...]
    methods: tuple[MethodName, ...]
    uses_real_seeds: Boolean
    uses_synthetic_seeds: Boolean


@dataclass(frozen=True)
class FullMethodSupportInputs:
    heldout_pfa_upper_bound: Probability
    target_pfa: Probability
    mean_strict_odi_rate: Probability
    minimum_strict_odi_rate: Probability
    paired_odi_advantage: OdiRateAdvantage
    minimum_odi_advantage: OdiRateAdvantage
    median_lead_among_successes: OperationalLeadEpochs
    minimum_median_lead: OperationalLeadEpochs
    directional_adjusted_p_value: Probability
    nominal_alpha: Probability
    full_operating_point_available: Boolean
    comparator_operating_point_available: Boolean


@dataclass(frozen=True)
class FullMethodSupportResult:
    pfa_criterion_satisfied: Boolean
    odi_rate_criterion_satisfied: Boolean
    advantage_criterion_satisfied: Boolean
    lead_criterion_satisfied: Boolean
    directional_criterion_satisfied: Boolean
    matched_operating_point_criterion_satisfied: Boolean

    @property
    def all_criteria_pass(self) -> Boolean:
        return (
            self.pfa_criterion_satisfied
            and self.odi_rate_criterion_satisfied
            and self.advantage_criterion_satisfied
            and self.lead_criterion_satisfied
            and self.directional_criterion_satisfied
            and self.matched_operating_point_criterion_satisfied
        )


def strict_odi_rate_criterion(mean_odi_rate: Probability, minimum_rate: Probability) -> Boolean:
    return mean_odi_rate >= minimum_rate


def paired_odi_advantage_criterion(
    paired_advantage: OdiRateAdvantage,
    minimum_advantage: OdiRateAdvantage,
) -> Boolean:
    return paired_advantage >= minimum_advantage


def median_operational_lead_criterion(
    median_lead_epochs: OperationalLeadEpochs,
    minimum_lead_epochs: OperationalLeadEpochs,
) -> Boolean:
    return median_lead_epochs >= minimum_lead_epochs


def median_of(values: tuple[OperationalLeadEpochs, ...]) -> OperationalLeadEpochs:
    if not values:
        raise ValueError("median requires at least one value")
    return statistics.median(values)


def matched_operating_point_requirement(
    full_method_available: Boolean,
    comparator_available: Boolean,
) -> Boolean:
    return full_method_available and comparator_available


def evaluate_full_method_support(inputs: FullMethodSupportInputs) -> FullMethodSupportResult:
    return FullMethodSupportResult(
        pfa_criterion_satisfied=inputs.heldout_pfa_upper_bound <= inputs.target_pfa,
        odi_rate_criterion_satisfied=strict_odi_rate_criterion(
            inputs.mean_strict_odi_rate, inputs.minimum_strict_odi_rate
        ),
        advantage_criterion_satisfied=paired_odi_advantage_criterion(
            inputs.paired_odi_advantage, inputs.minimum_odi_advantage
        ),
        lead_criterion_satisfied=median_operational_lead_criterion(
            inputs.median_lead_among_successes, inputs.minimum_median_lead
        ),
        directional_criterion_satisfied=inputs.directional_adjusted_p_value < inputs.nominal_alpha,
        matched_operating_point_criterion_satisfied=matched_operating_point_requirement(
            inputs.full_operating_point_available, inputs.comparator_operating_point_available
        ),
    )


def experiment_registry(config: ScientificConfig) -> tuple[ExperimentContract, ...]:
    experiments = config.experiments
    return (
        ExperimentContract(
            experiment_name=ExperimentName.SYNTHETIC_MODULE_VALIDATION,
            execution_roles=(ExecutionRole.VALIDATION,),
            methods=(),
            uses_real_seeds=False,
            uses_synthetic_seeds=False,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION,
            execution_roles=(ExecutionRole.DEVELOPMENT, ExecutionRole.CONFIRMATORY),
            methods=(),
            uses_real_seeds=False,
            uses_synthetic_seeds=True,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.PURE_ORDER_SEPARATION_VALIDATION,
            execution_roles=(ExecutionRole.DEVELOPMENT, ExecutionRole.CONFIRMATORY),
            methods=experiments.pure_order_separation_validation.methods,
            uses_real_seeds=False,
            uses_synthetic_seeds=True,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.EXCLUSION_MATCHED_HOFD_EQUIVALENCE,
            execution_roles=(ExecutionRole.DEVELOPMENT, ExecutionRole.CONFIRMATORY),
            methods=experiments.exclusion_matched_hofd_equivalence.methods,
            uses_real_seeds=False,
            uses_synthetic_seeds=True,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.STRONG_COMPARATOR_COMPOSITION_CHALLENGE,
            execution_roles=(ExecutionRole.DEVELOPMENT, ExecutionRole.DEVELOPMENT_ONLY),
            methods=experiments.strong_comparator_composition_challenge.candidates,
            uses_real_seeds=False,
            uses_synthetic_seeds=True,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.ESTIMATOR_SUPPORT_AND_CONTEXT_FEASIBILITY,
            execution_roles=(ExecutionRole.DEVELOPMENT, ExecutionRole.CONFIRMATORY),
            methods=(),
            uses_real_seeds=False,
            uses_synthetic_seeds=True,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.SEQUENTIAL_EVIDENCE_VALIDATION,
            execution_roles=(ExecutionRole.DEVELOPMENT, ExecutionRole.CONFIRMATORY),
            methods=(),
            uses_real_seeds=False,
            uses_synthetic_seeds=True,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.PRIMARY_STRICT_ODI_EVALUATION,
            execution_roles=(ExecutionRole.DEVELOPMENT, ExecutionRole.CONFIRMATORY),
            methods=experiments.primary_strict_odi_evaluation.methods,
            uses_real_seeds=True,
            uses_synthetic_seeds=False,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.EXCLUSION_MECHANISM_ABLATION,
            execution_roles=(ExecutionRole.DEVELOPMENT, ExecutionRole.CONFIRMATORY),
            methods=experiments.exclusion_mechanism_ablation.methods,
            uses_real_seeds=True,
            uses_synthetic_seeds=False,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.PURIFICATION_AND_ORDER_ABLATION,
            execution_roles=(ExecutionRole.DEVELOPMENT, ExecutionRole.CONFIRMATORY),
            methods=experiments.purification_and_order_ablation.methods,
            uses_real_seeds=True,
            uses_synthetic_seeds=False,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.CONTEXT_AND_ESTIMATOR_SENSITIVITY,
            execution_roles=(ExecutionRole.DEVELOPMENT_ONLY,),
            methods=(),
            uses_real_seeds=True,
            uses_synthetic_seeds=False,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS,
            execution_roles=(ExecutionRole.DEVELOPMENT, ExecutionRole.CONFIRMATORY),
            methods=experiments.benign_common_mode_robustness.methods,
            uses_real_seeds=True,
            uses_synthetic_seeds=False,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE,
            execution_roles=(ExecutionRole.DEVELOPMENT, ExecutionRole.CONFIRMATORY),
            methods=(MethodName.FULL_FEDCAMPAIGN_EMHI,),
            uses_real_seeds=True,
            uses_synthetic_seeds=False,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.SECONDARY_CONTROLLED_TRACE_GENERALIZATION,
            execution_roles=(ExecutionRole.DEVELOPMENT, ExecutionRole.CONFIRMATORY),
            methods=experiments.secondary_controlled_trace_generalization.methods,
            uses_real_seeds=True,
            uses_synthetic_seeds=False,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.OUTSIDE_CAMPAIGN_CONTAMINATION_BOUNDARY,
            execution_roles=(ExecutionRole.DEVELOPMENT, ExecutionRole.CONFIRMATORY),
            methods=(),
            uses_real_seeds=False,
            uses_synthetic_seeds=True,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.CLIENT_DROPOUT_AND_CONTEXT_SPARSITY_BOUNDARY,
            execution_roles=(ExecutionRole.DEVELOPMENT_ONLY,),
            methods=(),
            uses_real_seeds=False,
            uses_synthetic_seeds=True,
        ),
        ExperimentContract(
            experiment_name=ExperimentName.COALITION_SCALABILITY,
            execution_roles=(ExecutionRole.DEVELOPMENT, ExecutionRole.CONFIRMATORY),
            methods=(),
            uses_real_seeds=True,
            uses_synthetic_seeds=False,
        ),
    )


def resolve_experiment_name(slug: ArtifactFilename) -> ExperimentName:
    try:
        return ExperimentName(slug)
    except ValueError as error:
        raise ValueError(f"unknown experiment name {slug}") from error


def planned_seed_count(
    config: ScientificConfig, contract: ExperimentContract, role: ExecutionRole
) -> SeedCount:
    if contract.experiment_name is ExperimentName.SYNTHETIC_MODULE_VALIDATION:
        return 1
    if role is ExecutionRole.CONFIRMATORY:
        if contract.uses_synthetic_seeds:
            return len(config.randomness.synthetic_confirmatory_roots)
        if contract.uses_real_seeds:
            return len(config.randomness.real_confirmatory_roots)
        return 0
    if contract.uses_synthetic_seeds:
        return len(config.randomness.synthetic_development_roots)
    if contract.uses_real_seeds:
        return len(config.randomness.real_development_roots)
    return 0


def enumerate_experiment_plan(
    config: ScientificConfig,
) -> tuple[tuple[ExperimentName, ExecutionRole, SeedCount], ...]:
    planned: list[tuple[ExperimentName, ExecutionRole, SeedCount]] = []
    for contract in experiment_registry(config):
        for role in contract.execution_roles:
            planned.append(
                (contract.experiment_name, role, planned_seed_count(config, contract, role))
            )
    return tuple(planned)


def assert_known_experiment(config: ScientificConfig, experiment_name: ExperimentName) -> None:
    names = {contract.experiment_name for contract in experiment_registry(config)}
    if experiment_name not in names:
        raise ValueError(f"experiment {experiment_name.value} is not in the configured registry")


def confirmatory_completeness_within_tolerance(
    loaded: LoadedScientificConfiguration,
    expected: tuple[SeedValue, ...],
    observed_seeds: tuple[SeedValue, ...],
) -> Boolean:
    if any(seed not in expected for seed in observed_seeds):
        return False
    missing_count = sum(1 for seed in expected if seed not in observed_seeds)
    return missing_count <= loaded.values.runtime.required_confirmatory_missing_cell_tolerance
