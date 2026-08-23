from fedcampaign_emhi.artifacts.provenance import content_digest
from fedcampaign_emhi.artifacts.records import SeedSummaryRecord
from fedcampaign_emhi.domain.enums import ExecutionRole, ExperimentName, MethodName
from fedcampaign_emhi.domain.types import (
    ArtifactIdentity,
    ComponentName,
    FiniteFloat,
    MaterialDependencyFingerprint,
    RecordCount,
    SeedValue,
)


def seed_mean(values: tuple[FiniteFloat, ...]) -> FiniteFloat:
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
    method_values: tuple[FiniteFloat, ...],
    reference_values: tuple[FiniteFloat, ...] | None,
    source_evaluation_ids: tuple[ArtifactIdentity, ...],
    dependency_fingerprint: MaterialDependencyFingerprint,
) -> SeedSummaryRecord:
    method_value = seed_mean(method_values)
    reference_value = None if reference_values is None else seed_mean(reference_values)
    difference = None if reference_value is None else method_value - reference_value
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
) -> tuple[FiniteFloat, ...]:
    differences: list[FiniteFloat] = []
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
