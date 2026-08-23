from fedcampaign_emhi.config.schema import FrozenConfigModel
from fedcampaign_emhi.domain.enums import (
    ArtifactLifecycleState,
    ArtifactNamespace,
    ClaimIdentifier,
    ClaimState,
    ExecutionRole,
    ExperimentName,
    ExperimentState,
    MethodName,
    OverwritePolicy,
)
from fedcampaign_emhi.domain.types import (
    ArtifactIdentity,
    ByteCount,
    ClientId,
    ComponentName,
    ConfigurationDigest,
    FiniteFloat,
    MaterialDependencyFingerprint,
    Probability,
    RecordCount,
    RelativePath,
    ResumeStep,
    RuntimeSeconds,
    SeedCount,
    SeedValue,
)


class ArtifactManifest(FrozenConfigModel):
    artifact_id: ArtifactIdentity
    namespace: ArtifactNamespace
    experiment_name: ExperimentName | None
    relative_path: RelativePath
    content_digest: ConfigurationDigest
    material_fingerprint: MaterialDependencyFingerprint
    upstream_ids: tuple[ArtifactIdentity, ...]
    lifecycle_state: ArtifactLifecycleState


class CompletionRecord(FrozenConfigModel):
    state: ExperimentState
    mandatory_output_paths: tuple[RelativePath, ...]
    mandatory_output_hashes: tuple[ConfigurationDigest, ...]


class ScientificCellRecord(FrozenConfigModel):
    experiment_name: ExperimentName
    execution_role: ExecutionRole
    semantic_cell_path: RelativePath
    method_name: MethodName | None
    seed: SeedValue | None
    state: ExperimentState
    material_digest: ConfigurationDigest
    selected_client_ids: tuple[ClientId, ...]
    upstream_artifact_ids: tuple[ArtifactIdentity, ...]
    dependency_fingerprint: MaterialDependencyFingerprint
    runtime_seconds: RuntimeSeconds
    peak_rss_bytes: ByteCount
    application_payload_bytes: ByteCount
    completion_record: CompletionRecord


class DependencyIndexEntry(FrozenConfigModel):
    artifact_id: ArtifactIdentity
    semantic_path: RelativePath
    producer_contract: ComponentName
    producer_experiment: ExperimentName | None
    producer_cell: RelativePath | None
    dependency_fingerprint: MaterialDependencyFingerprint
    upstream_artifact_ids: tuple[ArtifactIdentity, ...]
    content_hashes: tuple[ConfigurationDigest, ...]
    active_state: ArtifactLifecycleState
    stale_reason: ComponentName | None
    downstream_consumers: tuple[ArtifactIdentity, ...]


class DependencyIndexRecord(FrozenConfigModel):
    entries: tuple[DependencyIndexEntry, ...]


class ExperimentRunRecord(FrozenConfigModel):
    experiment_name: ExperimentName
    material_digest: ConfigurationDigest
    overwrite_policy: OverwritePolicy
    resume_sequence: tuple[ResumeStep, ...]
    state: ExperimentState


class PlannedExperimentRecord(FrozenConfigModel):
    experiment_name: ExperimentName
    execution_role: ExecutionRole
    seed_count: SeedCount
    state: ExperimentState


class PlanArtifactRecord(FrozenConfigModel):
    material_digest: ConfigurationDigest
    resume_sequence: tuple[ResumeStep, ...]
    experiments: tuple[PlannedExperimentRecord, ...]


class SeedSummaryRecord(FrozenConfigModel):
    experiment_name: ExperimentName
    execution_role: ExecutionRole
    method_name: MethodName
    reference_method_name: MethodName | None
    metric_name: ComponentName
    seed: SeedValue
    method_value: FiniteFloat
    reference_value: FiniteFloat | None
    paired_difference: FiniteFloat | None
    campaign_count: RecordCount
    source_evaluation_ids: tuple[ArtifactIdentity, ...]
    dependency_fingerprint: MaterialDependencyFingerprint
    content_digest: ConfigurationDigest


class StatisticalRecord(FrozenConfigModel):
    hypothesis_identifier: ComponentName
    metric_name: ComponentName
    method_name: ComponentName
    independent_unit_count: RecordCount
    estimate: FiniteFloat
    raw_p_value: Probability | None
    adjusted_p_value: Probability | None
    confidence_level: Probability | None
    confidence_lower: FiniteFloat | None
    confidence_upper: FiniteFloat | None
    decision: ClaimState
    source_result_ids: tuple[ArtifactIdentity, ...]
    dependency_fingerprint: MaterialDependencyFingerprint
    content_digest: ConfigurationDigest


class ClaimRegistryEntry(FrozenConfigModel):
    claim_identifier: ClaimIdentifier
    exact_claim: ComponentName
    supporting_experiments: tuple[ExperimentName, ...]
    primary_metric: ComponentName
    secondary_metrics: tuple[ComponentName, ...]
    statistical_rule: ComponentName
    materiality_gate: ComponentName
    failure_condition: ComponentName
    valid_scope: ComponentName
    forbidden_extrapolation: ComponentName
    supporting_table: RelativePath | None
    supporting_figure: RelativePath | None
    state: ClaimState
    state_reason: ComponentName
    source_artifact_hashes: tuple[ConfigurationDigest, ...]


class ReportSourceRecord(FrozenConfigModel):
    source_analysis_hash: ConfigurationDigest
    report_dependency_fingerprint: MaterialDependencyFingerprint
    source_scientific_cell_paths: tuple[RelativePath, ...]
    source_artifact_hashes: tuple[ConfigurationDigest, ...]
