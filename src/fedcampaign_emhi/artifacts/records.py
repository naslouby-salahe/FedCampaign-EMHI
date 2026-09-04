from fedcampaign_emhi.config.schema import FrozenConfigModel
from fedcampaign_emhi.domain.enums import (
    ArtifactLifecycleState,
    ArtifactNamespace,
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
    DetectorFamily,
    ExecutionRole,
    ExperimentName,
    ExperimentState,
    FitStatus,
    GroundTruthClass,
    MethodName,
    OverwritePolicy,
)
from fedcampaign_emhi.domain.types import (
    ArtifactIdentity,
    BasisSize,
    BinIndex,
    Boolean,
    ByteCount,
    CellCount,
    ClientId,
    CommonModeSuppression,
    ComponentName,
    ConfigurationDigest,
    DetectionRateLoss,
    DetectorScore,
    EpochIndexValue,
    FalseAlarmRate,
    FeatureValue,
    InnovationCoordinate,
    InnovationDeviation,
    InnovationMean,
    MaterialDependencyFingerprint,
    MetricValue,
    NuisanceCoefficient,
    NumericalFloor,
    OperationalLeadEpochs,
    OperationalNormReference,
    PairedDifference,
    Probability,
    ProjectionNrmse,
    RankValue,
    RecordCount,
    RelativePath,
    ResumeStep,
    RidgePenalty,
    RobustnessCountMultiplier,
    RuntimeSeconds,
    SeedCount,
    SeedValue,
    StandardizedError,
    StandardizedNullBias,
    StatisticValue,
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


class ExperimentRunRecord(FrozenConfigModel):
    experiment_name: ExperimentName
    material_digest: ConfigurationDigest
    implementation_digest: ConfigurationDigest
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
    unscaled_feature_values: tuple[FeatureValue, ...] = ()
    feature_values: tuple[FeatureValue, ...]
    ground_truth: GroundTruthClass
    raw_event_count: RecordCount
    ambiguous_event_count: RecordCount


class ClientFeatureScalerRecord(FrozenConfigModel):
    client_id: ClientId
    medians: tuple[FeatureValue, ...]
    iqrs: tuple[FeatureValue, ...]
    iqr_floor: NumericalFloor


class PreparedDatasetRecord(FrozenConfigModel):
    dataset_name: DatasetName
    selected_client_ids: tuple[ClientId, ...] = ()
    eligible_client_ids: tuple[ClientId, ...] = ()
    has_sufficient_clients: Boolean = False
    epochs: tuple[PreparedEpochRecord, ...]
    client_scalers: tuple[ClientFeatureScalerRecord, ...] = ()
    excluded_record_count: RecordCount
    duplicate_record_count: RecordCount = 0
    ground_truth_discrepancy_count: RecordCount


class DatasetSplitRecord(FrozenConfigModel):
    dataset_name: DatasetName
    selected_client_ids: tuple[ClientId, ...]
    eligible_client_ids: tuple[ClientId, ...]
    has_sufficient_clients: Boolean
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
    scores: tuple[DetectorScore, ...]


class DetectorScoreArtifactRecord(FrozenConfigModel):
    dataset_name: DatasetName
    root_seed: SeedValue
    selected_client_ids: tuple[ClientId, ...]
    client_streams: tuple[ClientDetectorScoreStream, ...]
    dependency_fingerprint: MaterialDependencyFingerprint


class ClientMarginalRankStream(FrozenConfigModel):
    client_id: ClientId
    nuisance_reference_scores: tuple[DetectorScore, ...]
    epoch_indexes: tuple[EpochIndexValue, ...]
    ranks: tuple[RankValue, ...]


class MarginalRankArtifactRecord(FrozenConfigModel):
    dataset_name: DatasetName
    root_seed: SeedValue
    selected_client_ids: tuple[ClientId, ...]
    client_streams: tuple[ClientMarginalRankStream, ...]
    dependency_fingerprint: MaterialDependencyFingerprint


class OrderContextFitRecord(FrozenConfigModel):
    coalition_order: CoalitionOrder
    context_method: ContextMethodName
    centroids: tuple[tuple[InnovationCoordinate, ...], ...]
    state: FitStatus


class ConditionalRankReferenceRecord(FrozenConfigModel):
    client_id: ClientId
    context_cell: BinIndex
    reference_ranks: tuple[RankValue, ...]


class ProjectionCellFitRecord(FrozenConfigModel):
    context_cell: BinIndex
    conditional_rank_references: tuple[ConditionalRankReferenceRecord, ...]
    selected_ridge_penalty: RidgePenalty | None
    complete_nuisance_coefficients: tuple[tuple[NuisanceCoefficient, ...], ...]
    coordinate_means: tuple[InnovationMean, ...]
    coordinate_deviations: tuple[InnovationDeviation, ...]
    operational_norm_reference: OperationalNormReference | None
    state: FitStatus
    numerical_failure: Boolean


class CoalitionFitRecord(FrozenConfigModel):
    coalition_client_ids: tuple[ClientId, ...]
    coalition_order: CoalitionOrder
    cells: tuple[ProjectionCellFitRecord, ...]
    state: FitStatus


class EMHIFitArtifactRecord(FrozenConfigModel):
    dataset_name: DatasetName
    root_seed: SeedValue
    method_name: MethodName
    selected_client_ids: tuple[ClientId, ...]
    basis_size: BasisSize
    proper_subset_purification_enabled: Boolean
    forced_no_abstention: Boolean
    order_contexts: tuple[OrderContextFitRecord, ...]
    coalition_fits: tuple[CoalitionFitRecord, ...]
    dependency_fingerprint: MaterialDependencyFingerprint


class SeedSummaryRecord(FrozenConfigModel):
    experiment_name: ExperimentName
    execution_role: ExecutionRole
    method_name: MethodName
    reference_method_name: MethodName | None
    metric_name: ComponentName
    seed: SeedValue
    method_value: MetricValue
    reference_value: MetricValue | None
    paired_difference: PairedDifference | None
    campaign_count: RecordCount
    source_evaluation_ids: tuple[ArtifactIdentity, ...]
    dependency_fingerprint: MaterialDependencyFingerprint
    content_digest: ConfigurationDigest


class StatisticalRecord(FrozenConfigModel):
    hypothesis_identifier: ComponentName
    metric_name: ComponentName
    method_name: ComponentName
    independent_unit_count: RecordCount
    estimate: StatisticValue
    raw_p_value: Probability | None
    adjusted_p_value: Probability | None
    confidence_level: Probability | None
    confidence_lower: StatisticValue | None
    confidence_upper: StatisticValue | None
    hodges_lehmann_shift: StatisticValue | None = None
    equivalence_established: Boolean | None = None
    meets_threshold: Boolean
    source_result_ids: tuple[ArtifactIdentity, ...]
    dependency_fingerprint: MaterialDependencyFingerprint
    content_digest: ConfigurationDigest


class EstimatorFeasibilityAggregationRecord(FrozenConfigModel):
    experiment_name: ExperimentName
    independent_unit_count: RecordCount
    mean_context_coverage: Probability
    mean_projection_nrmse: ProjectionNrmse
    mean_standardized_null_bias: StandardizedNullBias
    numerical_failure_count: RecordCount
    attempted_condition_count: RecordCount
    pooled_numerical_failure_rate: Probability
    meets_threshold: Boolean
    source_result_ids: tuple[ArtifactIdentity, ...]
    dependency_fingerprint: MaterialDependencyFingerprint
    content_digest: ConfigurationDigest


class ContextEstimatorSensitivityMetrics(FrozenConfigModel):
    heldout_pfa: FalseAlarmRate | None
    campaign_detection_rate: Probability
    strict_odi_rate: Probability
    operational_lead_mean: OperationalLeadEpochs | None
    context_coverage: Probability
    abstention_rate: Probability
    numerical_failure_rate: Probability


class ContextEstimatorSensitivityCellRecord(FrozenConfigModel):
    seed: SeedValue
    basis_size_override: BasisSize | None
    context_cell_count_override: CellCount | None
    forced_ridge_override: RidgePenalty | None
    context_method_override: ContextMethodName | None
    condition: ContextEstimatorSensitivityMetrics
    base: ContextEstimatorSensitivityMetrics
    source_result_ids: tuple[ArtifactIdentity, ...]
    dependency_fingerprint: MaterialDependencyFingerprint
    content_digest: ConfigurationDigest


class CountStressDiagnosticRecord(FrozenConfigModel):
    seed: SeedValue
    multiplication_factor: RobustnessCountMultiplier
    emhi_false_declaration_rate: Probability
    raw_mean_false_declaration_rate: Probability
    source_result_ids: tuple[ArtifactIdentity, ...]
    dependency_fingerprint: MaterialDependencyFingerprint
    content_digest: ConfigurationDigest


class BenignCommonModePositivePowerMeasurementRecord(FrozenConfigModel):
    independent_unit_count: RecordCount
    mean_detection_rate_power_loss: DetectionRateLoss
    detection_rate_loss_within_maximum: Boolean
    mean_common_mode_suppression: CommonModeSuppression
    false_campaign_suppression_meets_minimum: Boolean
    source_result_ids: tuple[ArtifactIdentity, ...]
    dependency_fingerprint: MaterialDependencyFingerprint
    content_digest: ConfigurationDigest


class FiniteHorizonAggregationRecord(FrozenConfigModel):
    experiment_name: ExperimentName
    independent_unit_count: RecordCount
    operating_point_unavailable_count: RecordCount
    target_pfa: Probability
    maximum_heldout_upper_pfa: FalseAlarmRate | None
    meets_threshold: Boolean
    source_result_ids: tuple[ArtifactIdentity, ...]
    dependency_fingerprint: MaterialDependencyFingerprint
    content_digest: ConfigurationDigest


class ComparatorNullPfaRecord(FrozenConfigModel):
    method_name: MethodName
    heldout_false_stops: RecordCount
    heldout_horizons: RecordCount
    heldout_upper_pfa: FalseAlarmRate | None
    eligible: Boolean


class ComparatorTargetErrorRecord(FrozenConfigModel):
    method_name: MethodName
    native_target_order: CoalitionOrder
    mean_standardized_error: StandardizedError


class ComparatorRuntimeTiebreakRecord(FrozenConfigModel):
    method_name: MethodName
    median_runtime_seconds: RuntimeSeconds


class StrongComparatorCompositionRecord(FrozenConfigModel):
    selected_method: MethodName
    selected_native_order: CoalitionOrder
    eligible_candidates: tuple[MethodName, ...]
    candidate_native_orders: tuple[ComparatorTargetErrorRecord, ...]
    null_pfa_results: tuple[ComparatorNullPfaRecord, ...]
    target_error_results: tuple[ComparatorTargetErrorRecord, ...]
    runtime_tiebreak_results: tuple[ComparatorRuntimeTiebreakRecord, ...]
    selection_rule_hash: ConfigurationDigest
    source_artifact_hashes: tuple[ConfigurationDigest, ...]
    dependency_fingerprint: MaterialDependencyFingerprint
    content_digest: ConfigurationDigest


class HolmFamilyResultRecord(FrozenConfigModel):
    hypothesis_identifier: ComponentName
    raw_p_value: Probability | None
    holm_input_p_value: Probability
    adjusted_p_value: Probability | None
    meets_threshold: Boolean


class PrimaryHolmFamilyRecord(FrozenConfigModel):
    material_digest: ConfigurationDigest
    results: tuple[HolmFamilyResultRecord, ...]
    source_statistical_paths: tuple[RelativePath, ...]
    source_artifact_hashes: tuple[ConfigurationDigest, ...]
    content_digest: ConfigurationDigest


class SecondaryHolmFamilyRecord(FrozenConfigModel):
    material_digest: ConfigurationDigest
    results: tuple[HolmFamilyResultRecord, ...]
    source_statistical_paths: tuple[RelativePath, ...]
    source_artifact_hashes: tuple[ConfigurationDigest, ...]
    content_digest: ConfigurationDigest


class ReportSourceRecord(FrozenConfigModel):
    source_analysis_hash: ConfigurationDigest
    report_dependency_fingerprint: MaterialDependencyFingerprint
    source_scientific_cell_paths: tuple[RelativePath, ...]
    source_artifact_hashes: tuple[ConfigurationDigest, ...]
