from typing import cast

from fedcampaign_emhi.artifacts.storage import payload_digest
from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.types import (
    ArtifactDependencyNode,
    ArtifactIdentity,
    ConfigurationDigest,
    MaterialDependencyFingerprint,
)


def content_digest(payload: YamlNode) -> ConfigurationDigest:
    return payload_digest(payload)


def material_fingerprint(
    configuration_digest: ConfigurationDigest,
    upstream_digests: tuple[ConfigurationDigest, ...],
) -> MaterialDependencyFingerprint:
    payload: YamlNode = {
        "configuration_digest": configuration_digest,
        "upstream_digests": list(upstream_digests),
    }
    return payload_digest(payload)


def synthetic_invariant_boundary_digest(config: ScientificConfig) -> ConfigurationDigest:
    return payload_digest(
        cast(
            YamlNode,
            {
                "generators": config.generators.model_dump(mode="json"),
                "synthetic": config.synthetic.model_dump(mode="json"),
                "numerics": config.numerics.model_dump(mode="json"),
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
