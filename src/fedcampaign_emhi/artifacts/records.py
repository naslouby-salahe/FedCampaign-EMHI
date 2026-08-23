from fedcampaign_emhi.config.schema import FrozenConfigModel
from fedcampaign_emhi.domain.enums import (
    ArtifactLifecycleState,
    ArtifactNamespace,
    ClaimIdentifier,
    ClaimState,
    DatasetName,
    DetectorFamily,
    ExecutionRole,
    ExperimentName,
    ExperimentState,
    GroundTruthClass,
    MethodName,
    OverwritePolicy,
)
from fedcampaign_emhi.domain.types import (
    ArtifactIdentity,
    ByteCount,
    ClientId,
    ComponentName,
    ConfigurationDigest,
    EpochIndexValue,
    FiniteFloat,
    MaterialDependencyFingerprint,
    Probability,
    RankValue,
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


class DatasetInventoryFileRecord(FrozenConfigModel):
    relative_path: RelativePath
    sha256: ConfigurationDigest
    byte_count: ByteCount


class DatasetInventoryRecord(FrozenConfigModel):
    dataset_name: DatasetName
    files: tuple[DatasetInventoryFileRecord, ...]
    content_digest: ConfigurationDigest


class PreparedEpochRecord(FrozenConfigModel):
    dataset_name: DatasetName
    client_id: ClientId
    epoch_index: EpochIndexValue
    feature_values: tuple[FiniteFloat, ...]
    ground_truth: GroundTruthClass
    raw_event_count: RecordCount
    ambiguous_event_count: RecordCount


class PreparedDatasetRecord(FrozenConfigModel):
    dataset_name: DatasetName
    epochs: tuple[PreparedEpochRecord, ...]
    excluded_record_count: RecordCount
    ground_truth_discrepancy_count: RecordCount


class DatasetSplitRecord(FrozenConfigModel):
    dataset_name: DatasetName
    selected_client_ids: tuple[ClientId, ...]
    eligible_client_ids: tuple[ClientId, ...]
    claim_state: ClaimState
    detector_fit_epochs: tuple[EpochIndexValue, ...]
    nuisance_fit_epochs: tuple[EpochIndexValue, ...]
    threshold_calibration_epochs: tuple[EpochIndexValue, ...]
    heldout_benign_epochs: tuple[EpochIndexValue, ...]


class BenignHorizonRecord(FrozenConfigModel):
    start_epoch: EpochIndexValue
    epoch_indexes: tuple[EpochIndexValue, ...]


class BenignPartitionRecord(FrozenConfigModel):
    dataset_name: DatasetName
    calibration_horizons: tuple[BenignHorizonRecord, ...]
    heldout_horizons: tuple[BenignHorizonRecord, ...]


class CampaignRecord(FrozenConfigModel):
    start_epoch: EpochIndexValue
    end_epoch: EpochIndexValue
    participating_client_ids: tuple[ClientId, ...]
    integrity_checksum: ConfigurationDigest


class CampaignRegistryRecord(FrozenConfigModel):
    dataset_name: DatasetName
    campaigns: tuple[CampaignRecord, ...]


class ClientDetectorScoreStream(FrozenConfigModel):
    client_id: ClientId
    detector_family: DetectorFamily
    detector_seed: SeedValue
    epoch_indexes: tuple[EpochIndexValue, ...]
    scores: tuple[FiniteFloat, ...]


class DetectorScoreArtifactRecord(FrozenConfigModel):
    dataset_name: DatasetName
    root_seed: SeedValue
    selected_client_ids: tuple[ClientId, ...]
    client_streams: tuple[ClientDetectorScoreStream, ...]
    dependency_fingerprint: MaterialDependencyFingerprint


class ClientMarginalRankStream(FrozenConfigModel):
    client_id: ClientId
    nuisance_reference_scores: tuple[FiniteFloat, ...]
    epoch_indexes: tuple[EpochIndexValue, ...]
    ranks: tuple[RankValue, ...]


class MarginalRankArtifactRecord(FrozenConfigModel):
    dataset_name: DatasetName
    root_seed: SeedValue
    selected_client_ids: tuple[ClientId, ...]
    client_streams: tuple[ClientMarginalRankStream, ...]
    dependency_fingerprint: MaterialDependencyFingerprint


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
