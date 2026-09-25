from typing import cast

from fedcampaign_emhi.artifacts.records import CampaignRecord
from fedcampaign_emhi.artifacts.storage import payload_digest
from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import DatasetName, ExperimentName, ScientificSemanticDependency
from fedcampaign_emhi.domain.types import (
    ArtifactDependencyNode,
    ArtifactIdentity,
    ClientId,
    ConfigurationDigest,
    EpochIndexValue,
    FalseAlarmRate,
    MaterialDependencyFingerprint,
    SeedValue,
)

TON_PREPROCESSING_SEMANTICS = (
    ScientificSemanticDependency.TON_COMPLETE_RAW_ROW_IDENTITY,
    ScientificSemanticDependency.FULL_RELEASE_SOURCE_IP_COHORT_SELECTION,
    ScientificSemanticDependency.REAL_EPOCH_ASSIGNMENT,
    ScientificSemanticDependency.REAL_EVENT_FEATURE_AGGREGATION,
)
EDGE_PREPROCESSING_SEMANTICS = (
    ScientificSemanticDependency.EDGE_TIMESTAMP_INTERPRETATION,
    ScientificSemanticDependency.FULL_RELEASE_SOURCE_IP_COHORT_SELECTION,
    ScientificSemanticDependency.REAL_EPOCH_ASSIGNMENT,
    ScientificSemanticDependency.REAL_EVENT_FEATURE_AGGREGATION,
)
SHARED_PREPROCESSING_SEMANTICS = (
    ScientificSemanticDependency.CHRONOLOGICAL_BENIGN_SPLIT,
    ScientificSemanticDependency.NONOVERLAPPING_BENIGN_HORIZONS,
    ScientificSemanticDependency.CO_TEMPORAL_MIXED_CATEGORY_EPISODES,
)
REAL_CAMPAIGN_SEMANTICS = (
    *TON_PREPROCESSING_SEMANTICS,
    *SHARED_PREPROCESSING_SEMANTICS,
    ScientificSemanticDependency.DETECTOR_SCORING,
    ScientificSemanticDependency.EMPIRICAL_MARGINAL_RANKING,
    ScientificSemanticDependency.COMPLEMENT_RESTRICTED_NUISANCE_FIT,
    ScientificSemanticDependency.PURIFIED_INTERACTION_ESTIMATION,
    ScientificSemanticDependency.LOCAL_POLICY_CALIBRATION,
    ScientificSemanticDependency.FINITE_HORIZON_GLOBAL_CALIBRATION,
    ScientificSemanticDependency.MATCHED_FIXED_CAMPAIGN_REPLAY,
    ScientificSemanticDependency.STRICT_ODI_AND_CENSORING,
    ScientificSemanticDependency.PAIRED_SEED_LEVEL_AGGREGATION,
    ScientificSemanticDependency.SIGN_FLIP_AND_HOLM_ANALYSIS,
)
SYNTHETIC_SEMANTICS = (
    ScientificSemanticDependency.SYNTHETIC_GENERATOR_SEMANTICS,
    ScientificSemanticDependency.COMPLEMENT_RESTRICTED_NUISANCE_FIT,
    ScientificSemanticDependency.PURIFIED_INTERACTION_ESTIMATION,
    ScientificSemanticDependency.FINITE_HORIZON_GLOBAL_CALIBRATION,
    ScientificSemanticDependency.MATCHED_FIXED_CAMPAIGN_REPLAY,
    ScientificSemanticDependency.STRICT_ODI_AND_CENSORING,
    ScientificSemanticDependency.PAIRED_SEED_LEVEL_AGGREGATION,
    ScientificSemanticDependency.SIGN_FLIP_AND_HOLM_ANALYSIS,
)
_REAL_CAMPAIGN_EXPERIMENTS = frozenset(
    {
        ExperimentName.PRIMARY_STRICT_ODI_EVALUATION,
        ExperimentName.EXCLUSION_MECHANISM_ABLATION,
        ExperimentName.PURIFICATION_AND_ORDER_ABLATION,
        ExperimentName.CONTEXT_AND_ESTIMATOR_SENSITIVITY,
        ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS,
        ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE,
        ExperimentName.SECONDARY_CONTROLLED_TRACE_GENERALIZATION,
        ExperimentName.OUTSIDE_CAMPAIGN_CONTAMINATION_BOUNDARY,
        ExperimentName.CLIENT_DROPOUT_AND_CONTEXT_SPARSITY_BOUNDARY,
        ExperimentName.PRE_EVALUATION_COHORT_SELECTION_SENSITIVITY,
    }
)
_ROBUSTNESS_DIAGNOSTIC_EXPERIMENTS = frozenset(
    {
        ExperimentName.CONTEXT_AND_ESTIMATOR_SENSITIVITY,
        ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS,
        ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE,
        ExperimentName.OUTSIDE_CAMPAIGN_CONTAMINATION_BOUNDARY,
        ExperimentName.CLIENT_DROPOUT_AND_CONTEXT_SPARSITY_BOUNDARY,
    }
)


def experiment_semantic_dependencies(
    experiment_name: ExperimentName,
) -> tuple[ScientificSemanticDependency, ...]:
    if experiment_name in _REAL_CAMPAIGN_EXPERIMENTS:
        semantics: tuple[ScientificSemanticDependency, ...] = REAL_CAMPAIGN_SEMANTICS
        if experiment_name is ExperimentName.PRE_EVALUATION_COHORT_SELECTION_SENSITIVITY:
            semantics = tuple(
                ScientificSemanticDependency.PRE_EVALUATION_SOURCE_IP_COHORT_SELECTION
                if dependency
                is ScientificSemanticDependency.FULL_RELEASE_SOURCE_IP_COHORT_SELECTION
                else dependency
                for dependency in semantics
            )
        if experiment_name is ExperimentName.SECONDARY_CONTROLLED_TRACE_GENERALIZATION:
            semantics = (
                *EDGE_PREPROCESSING_SEMANTICS,
                *SHARED_PREPROCESSING_SEMANTICS,
                ScientificSemanticDependency.DETECTOR_SCORING,
                ScientificSemanticDependency.EMPIRICAL_MARGINAL_RANKING,
                ScientificSemanticDependency.COMPLEMENT_RESTRICTED_NUISANCE_FIT,
                ScientificSemanticDependency.PURIFIED_INTERACTION_ESTIMATION,
                ScientificSemanticDependency.LOCAL_POLICY_CALIBRATION,
                ScientificSemanticDependency.FINITE_HORIZON_GLOBAL_CALIBRATION,
                ScientificSemanticDependency.MATCHED_FIXED_CAMPAIGN_REPLAY,
                ScientificSemanticDependency.STRICT_ODI_AND_CENSORING,
                ScientificSemanticDependency.PAIRED_SEED_LEVEL_AGGREGATION,
                ScientificSemanticDependency.SIGN_FLIP_AND_HOLM_ANALYSIS,
            )
        if experiment_name in _ROBUSTNESS_DIAGNOSTIC_EXPERIMENTS:
            semantics = (*semantics, ScientificSemanticDependency.ROBUSTNESS_DIAGNOSTIC_SEMANTICS)
        return tuple(sorted(set(semantics)))
    if experiment_name is ExperimentName.COALITION_SCALABILITY:
        return (ScientificSemanticDependency.SCALABILITY_HARNESS_SEMANTICS,)
    semantics = SYNTHETIC_SEMANTICS
    if experiment_name in _ROBUSTNESS_DIAGNOSTIC_EXPERIMENTS:
        semantics = (*semantics, ScientificSemanticDependency.ROBUSTNESS_DIAGNOSTIC_SEMANTICS)
    return tuple(sorted(set(semantics)))


def semantic_dependency_digest(
    dependencies: tuple[ScientificSemanticDependency, ...],
) -> ConfigurationDigest:
    ordered = tuple(sorted(set(dependencies)))
    return payload_digest({"semantic_dependencies": list(ordered)})


def experiment_semantic_digest(experiment_name: ExperimentName) -> ConfigurationDigest:
    return semantic_dependency_digest(experiment_semantic_dependencies(experiment_name))


def real_campaign_comparison_contract_digest(
    config: ScientificConfig,
    dataset_name: DatasetName,
    seed: SeedValue,
    source_digests: tuple[ConfigurationDigest, ...],
    selected_client_ids: tuple[ClientId, ...],
    campaigns: tuple[CampaignRecord, ...],
    evaluation_epochs: tuple[tuple[EpochIndexValue, ...], ...],
    local_policy_target_pfa: FalseAlarmRate,
) -> ConfigurationDigest:
    if len(campaigns) != len(evaluation_epochs):
        raise ValueError("each campaign requires one locked replay epoch sequence")
    return payload_digest(
        cast(
            YamlNode,
            {
                "dataset_name": dataset_name,
                "seed": seed,
                "common_source_digests": list(source_digests),
                "selected_cohort": list(selected_client_ids),
                "campaign_registry": [
                    {
                        "start_epoch": campaign.start_epoch,
                        "end_epoch": campaign.end_epoch,
                        "participating_client_ids": list(campaign.participating_client_ids),
                        "attack_types": list(campaign.attack_types),
                        "evaluation_epoch_indexes": list(epochs),
                    }
                    for campaign, epochs in zip(campaigns, evaluation_epochs, strict=True)
                ],
                "local_policy": config.local_policy.model_dump(mode="json"),
                "local_policy_target_pfa": local_policy_target_pfa,
                "global_calibration": config.evidence.calibrated_finite_horizon.model_dump(
                    mode="json"
                ),
                "evaluation_horizon_epochs": config.campaign.evaluation_horizon_epochs,
                "strict_odi": ScientificSemanticDependency.STRICT_ODI_AND_CENSORING,
            },
        )
    )


def content_digest(payload: YamlNode) -> ConfigurationDigest:
    return payload_digest(payload)


def material_fingerprint(
    configuration_digest: ConfigurationDigest,
    upstream_digests: tuple[ConfigurationDigest, ...],
    semantic_dependencies: tuple[ScientificSemanticDependency, ...] = (),
) -> MaterialDependencyFingerprint:
    payload: YamlNode = {
        "configuration_digest": configuration_digest,
        "upstream_digests": list(upstream_digests),
    }
    if semantic_dependencies:
        payload["semantic_dependencies"] = [
            dependency for dependency in sorted(set(semantic_dependencies))
        ]
    return payload_digest(payload)


def synthetic_invariant_boundary_digest(config: ScientificConfig) -> ConfigurationDigest:
    return payload_digest(
        cast(
            YamlNode,
            {
                "generators": config.generators.model_dump(mode="json"),
                "synthetic": config.synthetic.model_dump(mode="json"),
                "context": config.context.model_dump(mode="json"),
                "basis": config.basis.model_dump(mode="json"),
                "projection": config.projection.model_dump(mode="json"),
                "evidence": config.evidence.model_dump(mode="json"),
                "distributed_support": config.distributed_support.model_dump(mode="json"),
                "campaign": config.campaign.model_dump(mode="json"),
                "engineering_smoke_root": config.randomness.engineering_smoke_root,
                "numerics": config.numerics.model_dump(mode="json"),
                "synthetic_module_validation": config.synthetic_module_validation.model_dump(
                    mode="json"
                ),
                "semantic_dependencies": [
                    ScientificSemanticDependency.SYNTHETIC_GENERATOR_SEMANTICS,
                    ScientificSemanticDependency.COMPLEMENT_RESTRICTED_NUISANCE_FIT,
                    ScientificSemanticDependency.PURIFIED_INTERACTION_ESTIMATION,
                ],
            },
        )
    )


def synthetic_cell_boundary_digest(config: ScientificConfig) -> ConfigurationDigest:
    return payload_digest(
        cast(
            YamlNode,
            {
                "generators": config.generators.model_dump(mode="json"),
                "synthetic": config.synthetic.model_dump(mode="json"),
                "context": config.context.model_dump(mode="json"),
                "basis": config.basis.model_dump(mode="json"),
                "projection": config.projection.model_dump(mode="json"),
                "study": config.study.model_dump(mode="json"),
                "comparators": config.comparators.model_dump(mode="json"),
                "evidence": config.evidence.model_dump(mode="json"),
                "numerics": config.numerics.model_dump(mode="json"),
                "experiments": {
                    "self_explanation_exclusion_validation": (
                        config.experiments.self_explanation_exclusion_validation.model_dump(
                            mode="json"
                        )
                    ),
                    "pure_order_separation_validation": (
                        config.experiments.pure_order_separation_validation.model_dump(mode="json")
                    ),
                    "exclusion_matched_hofd_equivalence": (
                        config.experiments.exclusion_matched_hofd_equivalence.model_dump(
                            mode="json"
                        )
                    ),
                    "estimator_support_and_context_feasibility": (
                        config.experiments.estimator_support_and_context_feasibility.model_dump(
                            mode="json"
                        )
                    ),
                    "sequential_evidence_validation": (
                        config.experiments.sequential_evidence_validation.model_dump(mode="json")
                    ),
                    "strong_comparator_composition_challenge": (
                        config.experiments.strong_comparator_composition_challenge.model_dump(
                            mode="json"
                        )
                    ),
                },
                "semantic_dependencies": list(SYNTHETIC_SEMANTICS),
            },
        )
    )


def nuisance_context_boundary_digest(config: ScientificConfig) -> ConfigurationDigest:
    return payload_digest(
        cast(
            YamlNode,
            {
                "context": {
                    "outside_lag_epochs": config.context.outside_lag_epochs,
                    "minimum_available_outside_clients": (
                        config.context.minimum_available_outside_clients
                    ),
                    "minimum_available_outside_fraction": (
                        config.context.minimum_available_outside_fraction
                    ),
                    "outside_histogram_bin_count": config.context.outside_histogram_bin_count,
                    "primary_cell_count": config.context.primary_cell_count,
                    "cell_count_sensitivity": config.context.cell_count_sensitivity,
                    "kmeans": config.context.kmeans.model_dump(mode="json"),
                    "minimum_support_epochs": config.context.minimum_support_epochs.model_dump(
                        mode="json"
                    ),
                    "nuisance_crossfit": config.context.nuisance_crossfit.model_dump(mode="json"),
                },
                "basis": config.basis.model_dump(mode="json"),
                "projection": config.projection.model_dump(mode="json"),
                "study": config.study.model_dump(mode="json"),
                "context_base_seed": config.randomness.context_base_seed,
                "semantic_dependencies": [
                    ScientificSemanticDependency.COMPLEMENT_RESTRICTED_NUISANCE_FIT,
                    ScientificSemanticDependency.PURIFIED_INTERACTION_ESTIMATION,
                ],
            },
        )
    )


def calibration_threshold_boundary_digest(config: ScientificConfig) -> ConfigurationDigest:
    return payload_digest(
        cast(
            YamlNode,
            {
                "evidence": {
                    "clip_bound": config.evidence.clip_bound,
                    "bet_lambda": config.evidence.bet_lambda,
                    "operational_norm_reference_quantile": (
                        config.evidence.operational_norm_reference_quantile
                    ),
                    "signed_theorem_sequential": (
                        config.evidence.signed_theorem_sequential.model_dump(mode="json")
                    ),
                    "calibrated_finite_horizon": (
                        config.evidence.calibrated_finite_horizon.model_dump(mode="json")
                    ),
                },
                "local_policy": config.local_policy.model_dump(mode="json"),
                "comparators": {
                    "common_calibration": config.comparators.common_calibration.model_dump(
                        mode="json"
                    ),
                },
                "study": config.study.model_dump(mode="json"),
                "semantic_dependencies": [
                    ScientificSemanticDependency.LOCAL_POLICY_CALIBRATION,
                    ScientificSemanticDependency.FINITE_HORIZON_GLOBAL_CALIBRATION,
                ],
            },
        )
    )


def campaign_evaluation_boundary_digest(config: ScientificConfig) -> ConfigurationDigest:
    return payload_digest(
        cast(
            YamlNode,
            {
                "campaign": config.campaign.model_dump(mode="json"),
                "distributed_support": config.distributed_support.model_dump(mode="json"),
                "numerics": config.numerics.model_dump(mode="json"),
                "semantic_dependencies": [
                    ScientificSemanticDependency.MATCHED_FIXED_CAMPAIGN_REPLAY,
                    ScientificSemanticDependency.STRICT_ODI_AND_CENSORING,
                ],
            },
        )
    )


def statistical_analysis_boundary_digest(config: ScientificConfig) -> ConfigurationDigest:
    return payload_digest(
        cast(
            YamlNode,
            {
                "statistics": config.statistics.model_dump(mode="json"),
                "materiality": config.materiality.model_dump(mode="json"),
                "statistical_analysis_base_seed": (
                    config.randomness.statistical_analysis_base_seed
                ),
                "semantic_dependencies": [
                    ScientificSemanticDependency.PAIRED_SEED_LEVEL_AGGREGATION,
                    ScientificSemanticDependency.SIGN_FLIP_AND_HOLM_ANALYSIS,
                ],
            },
        )
    )


def evidence_export_boundary_digest(config: ScientificConfig) -> ConfigurationDigest:
    return payload_digest(
        cast(
            YamlNode,
            {
                "reporting": config.reporting.model_dump(mode="json"),
                "experiments": {
                    "strong_comparator_composition_challenge": (
                        config.experiments.strong_comparator_composition_challenge.model_dump(
                            mode="json"
                        )
                    ),
                },
                "semantic_dependencies": [
                    ScientificSemanticDependency.REPORT_SOURCE_VALIDATION,
                ],
            },
        )
    )


def descendant_ids(
    graph: tuple[ArtifactDependencyNode, ...],
    changed_ids: tuple[ArtifactIdentity, ...],
) -> tuple[ArtifactIdentity, ...]:
    edges: list[tuple[ArtifactIdentity, ArtifactIdentity]] = []
    for node in graph:
        for upstream_id in node.upstream_ids:
            edges.append((upstream_id, node.artifact_id))
    discovered: list[ArtifactIdentity] = []
    pending: list[ArtifactIdentity] = list(changed_ids)
    seen: set[ArtifactIdentity] = set(changed_ids)
    while pending:
        current = pending.pop()
        for upstream_id, child in edges:
            if upstream_id != current or child in seen:
                continue
            seen.add(child)
            discovered.append(child)
            pending.append(child)
    return tuple(sorted(discovered))
