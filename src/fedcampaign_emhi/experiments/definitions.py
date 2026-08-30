from dataclasses import dataclass

from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, MethodName
from fedcampaign_emhi.domain.types import ArtifactFilename, Boolean


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


def loaded_experiment_registry(
    loaded: LoadedScientificConfiguration,
) -> tuple[ExperimentContract, ...]:
    return experiment_registry(loaded.values)
