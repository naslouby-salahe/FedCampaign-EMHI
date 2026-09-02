from pathlib import Path
from typing import cast

from fedcampaign_emhi.analysis.statistics import (
    HolmHypothesisInput,
    paired_difference,
    primary_holm_family,
)
from fedcampaign_emhi.artifacts.provenance import (
    content_digest,
    material_fingerprint,
    statistical_analysis_boundary_digest,
)
from fedcampaign_emhi.artifacts.records import (
    HolmFamilyResultRecord,
    PrimaryHolmFamilyRecord,
    SeedSummaryRecord,
    StatisticalRecord,
)
from fedcampaign_emhi.artifacts.storage import (
    build_artifact_layout,
    file_sha256,
    payload_digest,
    write_atomic_json,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    ExecutionRole,
    ExperimentName,
    MethodName,
    PrimaryHolmHypothesis,
)
from fedcampaign_emhi.domain.types import (
    ArtifactIdentity,
    ComponentName,
    MaterialDependencyFingerprint,
    MetricValue,
    PairedDifference,
    RecordCount,
    SeedValue,
)


def seed_mean(values: tuple[MetricValue, ...]) -> MetricValue:
    if not values:
        raise ValueError("seed summary requires at least one source value")
    return sum(values) / len(values)


def build_seed_summary(
    experiment_name: ExperimentName,
    execution_role: ExecutionRole,
    method_name: MethodName,
    reference_method_name: MethodName | None,
    metric_name: ComponentName,
    seed: SeedValue,
    method_values: tuple[MetricValue, ...],
    reference_values: tuple[MetricValue, ...] | None,
    source_evaluation_ids: tuple[ArtifactIdentity, ...],
    dependency_fingerprint: MaterialDependencyFingerprint,
) -> SeedSummaryRecord:
    method_value = seed_mean(method_values)
    reference_value = None if reference_values is None else seed_mean(reference_values)
    difference = (
        None
        if reference_value is None
        else paired_difference((method_value,), (reference_value,))[0]
    )
    campaign_count: RecordCount = len(method_values)
    digest = content_digest(
        {
            "experiment_name": experiment_name.value,
            "execution_role": execution_role.value,
            "method_name": method_name.value,
            "reference_method_name": None
            if reference_method_name is None
            else reference_method_name.value,
            "metric_name": metric_name,
            "seed": seed,
            "method_value": method_value,
            "reference_value": reference_value,
            "paired_difference": difference,
            "campaign_count": campaign_count,
            "source_evaluation_ids": list(source_evaluation_ids),
            "dependency_fingerprint": dependency_fingerprint,
        }
    )
    return SeedSummaryRecord(
        experiment_name=experiment_name,
        execution_role=execution_role,
        method_name=method_name,
        reference_method_name=reference_method_name,
        metric_name=metric_name,
        seed=seed,
        method_value=method_value,
        reference_value=reference_value,
        paired_difference=difference,
        campaign_count=campaign_count,
        source_evaluation_ids=source_evaluation_ids,
        dependency_fingerprint=dependency_fingerprint,
        content_digest=digest,
    )


def paired_seed_differences(
    summaries: tuple[SeedSummaryRecord, ...],
) -> tuple[PairedDifference, ...]:
    differences: list[PairedDifference] = []
    seen: set[SeedValue] = set()
    for summary in summaries:
        if summary.seed in seen:
            raise ValueError("seed summaries must contain one row per independent seed")
        seen.add(summary.seed)
        if summary.paired_difference is None:
            raise ValueError("paired inference requires paired seed summaries")
        differences.append(summary.paired_difference)
    if not differences:
        raise ValueError("paired inference requires at least one independent seed")
    return tuple(differences)


PRIMARY_HOLM_STATISTICS = (
    (
        ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION,
        PrimaryHolmHypothesis.SELF_EXPLANATION_MATERIAL_ATTENUATION,
    ),
    (
        ExperimentName.PURE_ORDER_SEPARATION_VALIDATION,
        PrimaryHolmHypothesis.PURE_ORDER_TARGET_DRIFT,
    ),
    (
        ExperimentName.PRIMARY_STRICT_ODI_EVALUATION,
        PrimaryHolmHypothesis.PRIMARY_ODI_ADVANTAGE_OVER_ORDER_AT_MOST_TWO_EMHI,
    ),
    (
        ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS,
        PrimaryHolmHypothesis.COMMON_MODE_FALSE_CAMPAIGN_REDUCTION,
    ),
    (
        ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE,
        PrimaryHolmHypothesis.STRONG_LOCAL_ODI_ABOVE_MINIMUM,
    ),
)


def _verified_statistical_record(
    loaded: LoadedScientificConfiguration, repository: Path, path: Path
) -> StatisticalRecord:
    record = StatisticalRecord.model_validate_json(path.read_bytes())
    source_paths = tuple(repository / source_id for source_id in record.source_result_ids)
    if not source_paths or any(not source_path.is_file() for source_path in source_paths):
        raise ValueError(f"statistical record {path} has missing source results")
    source_digests = tuple(file_sha256(source_path) for source_path in source_paths)
    if record.dependency_fingerprint != material_fingerprint(
        statistical_analysis_boundary_digest(loaded.values), source_digests
    ):
        raise ValueError(f"statistical record {path} has stale source lineage")
    return record


def materialize_primary_holm_family(
    loaded: LoadedScientificConfiguration, repository: Path
) -> Path:
    layout = build_artifact_layout(loaded, repository)
    paths: list[Path] = []
    inputs: list[HolmHypothesisInput] = []
    for experiment_name, hypothesis in PRIMARY_HOLM_STATISTICS:
        root = layout.experiment_outputs_root(experiment_name) / "statistics"
        matching = tuple(
            path
            for path in sorted(root.rglob("*.json"))
            if _verified_statistical_record(loaded, repository, path).hypothesis_identifier
            == hypothesis
        )
        if len(matching) != 1:
            raise FileNotFoundError(f"missing verified primary Holm statistic {hypothesis!s}")
        record = _verified_statistical_record(loaded, repository, matching[0])
        paths.append(matching[0])
        inputs.append(
            HolmHypothesisInput(
                identifier=hypothesis,
                raw_p_value=record.raw_p_value,
                decision=record.decision,
            )
        )
    results = primary_holm_family(tuple(inputs))
    relative_paths = tuple(path.relative_to(repository).as_posix() for path in paths)
    source_hashes = tuple(file_sha256(path) for path in paths)
    payload: YamlNode = {
        "material_digest": loaded.material_digest,
        "results": [
            {
                "hypothesis_identifier": result.identifier,
                "raw_p_value": result.raw_p_value,
                "holm_input_p_value": result.holm_input_p_value,
                "adjusted_p_value": result.adjusted_p_value,
                "decision": result.decision.value,
            }
            for result in results
        ],
        "source_statistical_paths": list(relative_paths),
        "source_artifact_hashes": list(source_hashes),
    }
    record = PrimaryHolmFamilyRecord(
        material_digest=loaded.material_digest,
        results=tuple(
            HolmFamilyResultRecord(
                hypothesis_identifier=result.identifier,
                raw_p_value=result.raw_p_value,
                holm_input_p_value=result.holm_input_p_value,
                adjusted_p_value=result.adjusted_p_value,
                decision=result.decision,
            )
            for result in results
        ),
        source_statistical_paths=relative_paths,
        source_artifact_hashes=source_hashes,
        content_digest=payload_digest(payload),
    )
    path = (
        layout.roots.results_root
        / "project_summary"
        / "statistics"
        / "multiplicity"
        / "primary-holm.json"
    )
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    return path
