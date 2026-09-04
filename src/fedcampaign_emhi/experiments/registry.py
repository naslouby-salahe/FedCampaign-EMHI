from dataclasses import dataclass

from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, MethodName
from fedcampaign_emhi.domain.types import (
    ArtifactFilename,
    Boolean,
    ResumeStep,
    SeedCount,
    SeedValue,
)

RESUME_SEQUENCE: tuple[ResumeStep, ...] = (
    "validate required existing artifacts",
    "reuse compatible ancestors",
    "identify incompatible or incomplete artifacts",
    "invalidate only their descendants",
    "reconstruct the minimum required subgraph",
    "atomically publish completed outputs",
)


@dataclass(frozen=True)
class ExperimentContract:
    experiment_name: ExperimentName
    execution_roles: tuple[ExecutionRole, ...]
    methods: tuple[MethodName, ...]
    uses_real_seeds: Boolean
    uses_synthetic_seeds: Boolean


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
