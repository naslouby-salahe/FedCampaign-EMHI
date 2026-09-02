from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ConfigurationProfile,
    ContextMethodName,
    DatasetName,
    GeneratorName,
    MethodName,
    NuisanceTransformName,
)
from fedcampaign_emhi.domain.types import (
    ArtifactFilename,
    AttenuationDifference,
    AutoencoderBeta,
    BasisSize,
    BatchSize,
    BettingLambda,
    BinCount,
    Boolean,
    BootstrapReplicateCount,
    CellCount,
    ClientCount,
    ClientLoading,
    CompensatorValue,
    ConcurrentExperimentCellCount,
    ConditionNumberLimit,
    ConfidenceLevel,
    ConfigSourcePath,
    ConfigurationDigest,
    Correlation,
    CosineSimilarity,
    CusumDriftSubtraction,
    CusumInitialState,
    DecimalPlaces,
    DetectionRateLoss,
    EffectCoefficient,
    EpochCount,
    EpochSeconds,
    ESrThreshold,
    EstimatorEvaluationSampleCount,
    EstimatorSupportLevel,
    EvidenceClipBound,
    EvidenceFactor,
    FactorRank,
    FalseAlarmRate,
    FeatureDimension,
    FeatureFraction,
    FederatedRoundCount,
    FiniteHorizonCalibrationCount,
    FiniteHorizonHeldoutNullCount,
    FoldCount,
    HashBucketCount,
    HofdEquivalenceSampleCount,
    InteractionStrength,
    IpfIterationLimit,
    JeffreysPseudocount,
    KmeansFitRowLimit,
    KmeansInitializationCount,
    LatentAutoregressiveCoefficient,
    LearningRate,
    MaterialOdiContribution,
    MemoryMib,
    MinimumNonoverlappingHorizonCount,
    MissingCellTolerance,
    MixedOrderTermIndex,
    NumericalFloor,
    NumericalTolerance,
    OdiRateAdvantage,
    OperationalLeadEpochs,
    Percentile,
    PositiveEpochCount,
    Probability,
    ProjectionNrmse,
    PureOrderEvaluationSampleCount,
    Quantile,
    RankValue,
    RecordCount,
    RelativePath,
    RequiredExceedanceCount,
    RetryCount,
    RidgePenalty,
    RobustnessCountMultiplier,
    RuntimeSeconds,
    SampleCap,
    ScalabilityRepetitionCount,
    ScoreShift,
    SeedCount,
    SeedValue,
    SignFlipAssignmentCount,
    SolverIterationLimit,
    StandardDeviation,
    StandardizedDrift,
    StandardizedNullBias,
    StoppingTimeDifferenceEpochs,
    SvmCoefficientZero,
    ThresholdValue,
    TrajectoryCount,
    TreeCount,
    WeightDecay,
    WorkerCount,
)


class FrozenConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class StudyConfig(FrozenConfigModel):
    maximum_coalition_order: CoalitionOrder


class TimeConfig(FrozenConfigModel):
    real_data_epoch_seconds: EpochSeconds


class CampaignConfig(FrozenConfigModel):
    evaluation_horizon_epochs: PositiveEpochCount
    prestart_warmup_epochs: PositiveEpochCount
    merge_max_intervening_benign_epochs: EpochCount
    distributed_first_activity_window_epochs: PositiveEpochCount
    minimum_duration_epochs: PositiveEpochCount


class DistributedSupportConfig(FrozenConfigModel):
    minimum_clients: ClientCount
    trailing_window_epochs: PositiveEpochCount
    material_coalition_evidence_threshold: EvidenceFactor


class ContextKmeansConfig(FrozenConfigModel):
    n_init: KmeansInitializationCount
    max_iterations: SolverIterationLimit
    tolerance: NumericalTolerance
    max_fit_rows: KmeansFitRowLimit
    assignment_tie_tolerance: NumericalTolerance


class ContextMinimumSupportEpochsConfig(FrozenConfigModel):
    order_one: PositiveEpochCount
    order_two: PositiveEpochCount
    order_three: PositiveEpochCount


class ContextNuisanceCrossfitConfig(FrozenConfigModel):
    fold_count: FoldCount


class ContextConfig(FrozenConfigModel):
    outside_lag_epochs: PositiveEpochCount
    minimum_available_outside_clients: ClientCount
    minimum_available_outside_fraction: Probability
    rank_clip_epsilon: NumericalFloor
    outside_histogram_bin_count: BinCount
    primary_cell_count: CellCount
    cell_count_sensitivity: tuple[CellCount, ...]
    kmeans: ContextKmeansConfig
    minimum_support_epochs: ContextMinimumSupportEpochsConfig
    nuisance_crossfit: ContextNuisanceCrossfitConfig


class BasisConfig(FrozenConfigModel):
    primary_size: BasisSize
    sensitivity_sizes: tuple[BasisSize, ...]


class ProjectionCrossValidationConfig(FrozenConfigModel):
    fold_count: FoldCount


class ProjectionConfig(FrozenConfigModel):
    ridge_candidates: tuple[RidgePenalty, ...]
    cross_validation: ProjectionCrossValidationConfig
    selection_tie_tolerance_mse: NumericalTolerance
    zero_ridge_svd_relative_cutoff: NumericalFloor
    maximum_gram_condition_number: ConditionNumberLimit
    atom_scale_floor: NumericalFloor
    norm_reference_floor: NumericalFloor

    @model_validator(mode="after")
    def _validate_ridge_candidates(self) -> Self:
        if 0.0 not in self.ridge_candidates:
            raise ValueError("ridge_candidates must include 0.0")
        return self


class EvidenceSignedTheoremSequentialConfig(FrozenConfigModel):
    arl_alpha: FalseAlarmRate


class EvidenceCalibratedFiniteHorizonConfig(FrozenConfigModel):
    target_pfa: FalseAlarmRate
    calibration_confidence: ConfidenceLevel
    threshold_candidates: tuple[ThresholdValue, ...]


class EvidenceConfig(FrozenConfigModel):
    clip_bound: EvidenceClipBound
    bet_lambda: BettingLambda
    operational_norm_reference_quantile: Quantile
    signed_theorem_sequential: EvidenceSignedTheoremSequentialConfig
    calibrated_finite_horizon: EvidenceCalibratedFiniteHorizonConfig
    no_stop_plot_offset_epochs: PositiveEpochCount


class DatasetsPrimaryConfig(FrozenConfigModel):
    name: DatasetName
    raw_directory: RelativePath
    target_client_count: ClientCount


class DatasetsSecondaryConfig(FrozenConfigModel):
    name: DatasetName
    raw_directory: RelativePath
    target_client_count: ClientCount
    minimum_eligible_client_count: ClientCount


class DatasetsEligibilityConfig(FrozenConfigModel):
    minimum_benign_event_records: RecordCount
    minimum_nonempty_benign_epochs: PositiveEpochCount


class DatasetsPreprocessingBenignPartitionFractionsConfig(FrozenConfigModel):
    detector_fit: Probability
    nuisance_fit: Probability
    threshold_and_policy_calibration: Probability

    @model_validator(mode="after")
    def _validate_bounds(self) -> Self:
        if self.detector_fit <= 0.0 or self.nuisance_fit <= 0.0:
            raise ValueError("benign partition fractions must be positive")
        if self.threshold_and_policy_calibration <= 0.0:
            raise ValueError("benign partition fractions must be positive")
        fraction_sum = self.detector_fit + self.nuisance_fit + self.threshold_and_policy_calibration
        if fraction_sum >= 1.0:
            raise ValueError(
                "heldout_benign is the chronological remainder and is not independently configurable"
            )
        return self


class DatasetsPreprocessingConfig(FrozenConfigModel):
    event_type_hash_bucket_count: HashBucketCount
    robust_scaling_iqr_floor: NumericalFloor
    benign_partition_fractions: DatasetsPreprocessingBenignPartitionFractionsConfig


class DatasetsConfig(FrozenConfigModel):
    primary: DatasetsPrimaryConfig
    secondary: DatasetsSecondaryConfig
    external_checksums_directory: RelativePath
    eligibility: DatasetsEligibilityConfig
    preprocessing: DatasetsPreprocessingConfig

    @model_validator(mode="after")
    def _validate_distinct_datasets(self) -> Self:
        if self.primary.name == self.secondary.name:
            raise ValueError("primary and secondary datasets must differ")
        return self


class DetectorsIsolationForestConfig(FrozenConfigModel):
    trees: TreeCount
    max_samples_cap: SampleCap
    max_features: FeatureFraction
    jobs: WorkerCount


class DetectorsOneClassSvmConfig(FrozenConfigModel):
    nu: Probability
    coefficient_zero: SvmCoefficientZero
    solver_tolerance: NumericalTolerance
    kernel_cache_mib: MemoryMib
    max_iterations: SolverIterationLimit


class DetectorsAutoencoderConfig(FrozenConfigModel):
    learning_rate: LearningRate
    betas: tuple[AutoencoderBeta, ...]
    optimizer_epsilon: NumericalFloor
    weight_decay: WeightDecay
    batch_size: BatchSize
    epochs: PositiveEpochCount


class DetectorsConfig(FrozenConfigModel):
    isolation_forest: DetectorsIsolationForestConfig
    one_class_svm: DetectorsOneClassSvmConfig
    autoencoder: DetectorsAutoencoderConfig


class LocalPolicyCandidatePersistenceConfig(FrozenConfigModel):
    required_exceedances: RequiredExceedanceCount
    window_epochs: PositiveEpochCount


class LocalPolicyConfig(FrozenConfigModel):
    candidate_score_quantiles: tuple[Quantile, ...]
    candidate_persistence: tuple[LocalPolicyCandidatePersistenceConfig, ...]
    primary_horizon_pfa_target: FalseAlarmRate
    strong_horizon_pfa_target: FalseAlarmRate
    pfa_confidence: ConfidenceLevel

    @model_validator(mode="after")
    def _validate_candidate_persistence(self) -> Self:
        persistence = tuple(
            (item.required_exceedances, item.window_epochs) for item in self.candidate_persistence
        )
        if persistence != ((1, 1), (2, 3), (3, 5)):
            raise ValueError(
                "candidate persistence must be the fixed 1-of-1, 2-of-3, 3-of-5 sequence"
            )
        return self


class RandomnessConfig(FrozenConfigModel):
    synthetic_development_roots: tuple[SeedValue, ...]
    synthetic_confirmatory_roots: tuple[SeedValue, ...]
    real_development_roots: tuple[SeedValue, ...]
    real_confirmatory_roots: tuple[SeedValue, ...]
    engineering_smoke_root: SeedValue
    statistical_analysis_base_seed: SeedValue
    context_base_seed: SeedValue


class SyntheticSampleSizesConfig(FrozenConfigModel):
    generic_nuisance_fit_epochs: PositiveEpochCount
    generic_cross_fitted_evaluation_epochs: PositiveEpochCount
    finite_horizon_calibration_horizons_per_seed: FiniteHorizonCalibrationCount
    finite_horizon_heldout_null_horizons_per_seed: FiniteHorizonHeldoutNullCount
    self_explanation_epochs_per_perturbation: PositiveEpochCount
    self_explanation_lag_settling_epochs_discarded: EpochCount
    pure_order_independent_evaluation_samples_per_condition_seed: PureOrderEvaluationSampleCount
    hofd_equivalence_heldout_samples_per_context_seed: HofdEquivalenceSampleCount
    estimator_evaluation_samples_per_context_seed: EstimatorEvaluationSampleCount


class SyntheticConfig(FrozenConfigModel):
    sample_sizes: SyntheticSampleSizesConfig


class GeneratorsCommonModeConfig(FrozenConfigModel):
    latent_ar_coefficient: LatentAutoregressiveCoefficient
    client_loading_minimum: ClientLoading
    client_loading_maximum: ClientLoading
    client_noise_standard_deviation: StandardDeviation


class GeneratorsControlledCampaignsMarginalConfig(FrozenConfigModel):
    score_shift: ScoreShift


class GeneratorsControlledCampaignsPairRelationConfig(FrozenConfigModel):
    benign_correlation: Correlation
    campaign_correlation: Correlation


class GeneratorsControlledCampaignsSingleClientConfig(FrozenConfigModel):
    score_shift: ScoreShift


class GeneratorsControlledCampaignsConfig(FrozenConfigModel):
    marginal: GeneratorsControlledCampaignsMarginalConfig
    pair_relation: GeneratorsControlledCampaignsPairRelationConfig
    single_client: GeneratorsControlledCampaignsSingleClientConfig


class GeneratorsSelfExplanationConfig(FrozenConfigModel):
    perturbations: tuple[ScoreShift, ...]
    derivative_regression_perturbations: tuple[ScoreShift, ...]


class GeneratorsPurePolynomialThetaConfig(FrozenConfigModel):
    order_one: tuple[EffectCoefficient, ...]
    order_two: tuple[EffectCoefficient, ...]
    order_three: tuple[EffectCoefficient, ...]


class GeneratorsPurePolynomialConfig(FrozenConfigModel):
    theta: GeneratorsPurePolynomialThetaConfig
    primary_reference_theta: EffectCoefficient


class GeneratorsXorConfig(FrozenConfigModel):
    strengths: tuple[InteractionStrength, ...]
    primary_reference_strength: InteractionStrength


class GeneratorsMixedOrderConfig(FrozenConfigModel):
    enabled_term_sets: tuple[tuple[MixedOrderTermIndex, ...], ...]
    term_coefficient: EffectCoefficient


class GeneratorsContextDependentTripleInitialStateProbabilitiesConfig(FrozenConfigModel):
    negative_one: Probability
    positive_one: Probability


class GeneratorsContextDependentTripleOutsideRankIntervalsConfig(FrozenConfigModel):
    negative_state: tuple[RankValue, ...]
    positive_state: tuple[RankValue, ...]


class GeneratorsContextDependentTripleConfig(FrozenConfigModel):
    markov_same_probability: Probability
    initial_state_probabilities: GeneratorsContextDependentTripleInitialStateProbabilitiesConfig
    primary_theta: EffectCoefficient
    outside_rank_intervals: GeneratorsContextDependentTripleOutsideRankIntervalsConfig


class GeneratorsOutsideContaminationConfig(FrozenConfigModel):
    client_count: ClientCount
    target_triple_theta: EffectCoefficient
    correlated_campaign_fractions: tuple[Probability, ...]
    outside_rank_shift: ScoreShift


class GeneratorsClientDropoutConfig(FrozenConfigModel):
    unavailable_fractions: tuple[Probability, ...]


class GeneratorsConfig(FrozenConfigModel):
    common_mode: GeneratorsCommonModeConfig
    controlled_campaigns: GeneratorsControlledCampaignsConfig
    self_explanation: GeneratorsSelfExplanationConfig
    pure_polynomial: GeneratorsPurePolynomialConfig
    xor: GeneratorsXorConfig
    mixed_order: GeneratorsMixedOrderConfig
    context_dependent_triple: GeneratorsContextDependentTripleConfig
    outside_contamination: GeneratorsOutsideContaminationConfig
    client_dropout: GeneratorsClientDropoutConfig


class ComparatorsCommonCalibrationConfig(FrozenConfigModel):
    nuisance_reference_quantile: Quantile


class ComparatorsConnectedInformationConfig(FrozenConfigModel):
    bins_per_client: BinCount
    jeffreys_pseudocount_per_cell: JeffreysPseudocount
    ipf_max_iterations: IpfIterationLimit
    maximum_marginal_absolute_error: NumericalTolerance
    probability_floor: NumericalFloor


class ComparatorsConditionalLogLinearConfig(FrozenConfigModel):
    bins_per_client: BinCount
    max_iterations: SolverIterationLimit
    maximum_fitted_marginal_absolute_error: NumericalTolerance
    probability_floor: NumericalFloor


class ComparatorsExclusionMatchedConditionalHofdConfig(FrozenConfigModel):
    relative_singular_cutoff: NumericalFloor
    ridge_penalty: RidgePenalty


class ComparatorsGlobalFactorResidualConfig(FrozenConfigModel):
    candidate_ranks: tuple[FactorRank, ...]
    cumulative_variance_target: Probability
    fallback_rank: FactorRank


class ComparatorsMultistreamCusumConfig(FrozenConfigModel):
    rank_center: RankValue
    drift_subtraction: CusumDriftSubtraction
    initial_state: CusumInitialState


class ComparatorsFedavgAutoencoderConfig(FrozenConfigModel):
    rounds: FederatedRoundCount
    local_epochs_per_round: PositiveEpochCount
    client_participation_fraction: Probability


class ComparatorsConfig(FrozenConfigModel):
    common_calibration: ComparatorsCommonCalibrationConfig
    connected_information: ComparatorsConnectedInformationConfig
    conditional_log_linear: ComparatorsConditionalLogLinearConfig
    exclusion_matched_conditional_hofd: ComparatorsExclusionMatchedConditionalHofdConfig
    global_factor_residual: ComparatorsGlobalFactorResidualConfig
    multistream_cusum: ComparatorsMultistreamCusumConfig
    fedavg_autoencoder: ComparatorsFedavgAutoencoderConfig


class NumericsConfig(FrozenConfigModel):
    metric_denominator_floor: NumericalFloor
    deterministic_comparison_tolerance: NumericalTolerance
    smoke_repeatability_tolerance: NumericalTolerance


class StatisticsConfig(FrozenConfigModel):
    confidence_level: ConfidenceLevel
    nominal_significance_alpha: FalseAlarmRate
    bootstrap_replicates: BootstrapReplicateCount
    synthetic_sign_flip_replicates_when_not_exact: BootstrapReplicateCount


class MaterialitySelfExplanationConfig(FrozenConfigModel):
    exact_exclusion_nuisance_derivative_equivalence_fraction_of_direct: Probability
    minimum_attenuation_difference: AttenuationDifference


class MaterialityPureOrderConfig(FrozenConfigModel):
    maximum_proper_subset_standardized_drift: StandardizedDrift
    minimum_target_order_standardized_drift: StandardizedDrift


class MaterialityOrderThreeEstimatorConfig(FrozenConfigModel):
    minimum_mean_context_coverage: Probability
    maximum_mean_projection_nrmse: ProjectionNrmse
    maximum_mean_standardized_null_bias: StandardizedNullBias


class MaterialityHofdEquivalenceConfig(FrozenConfigModel):
    atom_nrmse_upper_margin: ProjectionNrmse
    minimum_cosine_similarity: CosineSimilarity
    stopping_time_difference_interval_epochs: tuple[StoppingTimeDifferenceEpochs, ...]


class MaterialityPrimaryRealConfig(FrozenConfigModel):
    minimum_strict_odi_rate: Probability
    minimum_odi_rate_advantage_over_order_at_most_two: OdiRateAdvantage
    minimum_median_operational_lead_epochs: OperationalLeadEpochs


class MaterialityBenignCommonModeConfig(FrozenConfigModel):
    minimum_false_campaign_suppression: Probability
    maximum_detection_rate_loss: DetectionRateLoss


class MaterialityStrongLocalConfig(FrozenConfigModel):
    minimum_strict_odi_rate: Probability


class MaterialityOrderThreeRealConfig(FrozenConfigModel):
    minimum_material_odi_contribution: MaterialOdiContribution


class MaterialityReferenceHarnessConfig(FrozenConfigModel):
    p95_latency_maximum_seconds: RuntimeSeconds


class MaterialityConfig(FrozenConfigModel):
    self_explanation: MaterialitySelfExplanationConfig
    pure_order: MaterialityPureOrderConfig
    order_three_estimator: MaterialityOrderThreeEstimatorConfig
    maximum_pooled_numerical_failure_rate: Probability
    hofd_equivalence: MaterialityHofdEquivalenceConfig
    primary_real: MaterialityPrimaryRealConfig
    benign_common_mode: MaterialityBenignCommonModeConfig
    strong_local: MaterialityStrongLocalConfig
    order_three_real: MaterialityOrderThreeRealConfig
    reference_harness: MaterialityReferenceHarnessConfig


class SupportGridsConfig(FrozenConfigModel):
    estimator_samples_per_context: tuple[EstimatorSupportLevel, ...]
    hofd_equivalence_samples_per_context: tuple[EstimatorSupportLevel, ...]
    estimator_one_factor_sensitivity_samples_per_context: tuple[EstimatorSupportLevel, ...]


class RobustnessConfig(FrozenConfigModel):
    benign_count_multiplication_factors: tuple[RobustnessCountMultiplier, ...]
    scalability_client_counts: tuple[ClientCount, ...]


class ExperimentsSelfExplanationExclusionValidationPrimaryConditionConfig(FrozenConfigModel):
    client_count: ClientCount
    coalition_order: CoalitionOrder
    nuisance_transform: NuisanceTransformName
    comparison: tuple[ContextMethodName, ...]


class ExperimentsSelfExplanationExclusionValidationConfig(FrozenConfigModel):
    context_methods: tuple[ContextMethodName, ...]
    primary_condition: ExperimentsSelfExplanationExclusionValidationPrimaryConditionConfig


class ExperimentsPureOrderSeparationValidationPrimaryConditionConfig(FrozenConfigModel):
    generator: GeneratorName
    method: MethodName
    coalition_order: CoalitionOrder


class ExperimentsPureOrderSeparationValidationConfig(FrozenConfigModel):
    primary_client_count: ClientCount
    generators: tuple[GeneratorName, ...]
    methods: tuple[MethodName, ...]
    primary_condition: ExperimentsPureOrderSeparationValidationPrimaryConditionConfig


class ExperimentsExclusionMatchedHofdEquivalenceConfig(FrozenConfigModel):
    methods: tuple[MethodName, ...]
    context_cell_count: CellCount
    primary_support_levels: tuple[EstimatorSupportLevel, ...]


class ExperimentsStrongComparatorCompositionChallengeConfig(FrozenConfigModel):
    candidates: tuple[MethodName, ...]
    error_tie_tolerance_standardized_units: NumericalTolerance
    runtime_tie_tolerance_seconds: RuntimeSeconds
    artifact_filename: ArtifactFilename


class ExperimentsEstimatorSupportAndContextFeasibilitySensitivityConfig(FrozenConfigModel):
    forced_ridge: RidgePenalty
    forced_no_abstention: Boolean


class ExperimentsEstimatorSupportAndContextFeasibilityConfig(FrozenConfigModel):
    sensitivity: ExperimentsEstimatorSupportAndContextFeasibilitySensitivityConfig


class ExperimentsSequentialEvidenceValidationSignedTheoremConfig(FrozenConfigModel):
    null_theta: EffectCoefficient
    trajectories_per_seed: TrajectoryCount
    maximum_trajectory_epochs: PositiveEpochCount
    restricted_arl_bootstrap_lower_bound_minimum_epochs: PositiveEpochCount


class ExperimentsSequentialEvidenceValidationConfig(FrozenConfigModel):
    signed_theorem: ExperimentsSequentialEvidenceValidationSignedTheoremConfig


class ExperimentsPrimaryStrictOdiEvaluationConfig(FrozenConfigModel):
    methods: tuple[MethodName, ...]


class ExperimentsExclusionMechanismAblationConfig(FrozenConfigModel):
    methods: tuple[MethodName, ...]


class ExperimentsPurificationAndOrderAblationConfig(FrozenConfigModel):
    methods: tuple[MethodName, ...]


class ExperimentsContextAndEstimatorSensitivityConfig(FrozenConfigModel):
    forced_ridge: RidgePenalty
    context_variants: tuple[ContextMethodName, ...]


class ExperimentsBenignCommonModeRobustnessNativeHighVolumeWindowConfig(FrozenConfigModel):
    stride_epochs: PositiveEpochCount
    top_event_count_fraction: Probability


class ExperimentsBenignCommonModeRobustnessConfig(FrozenConfigModel):
    methods: tuple[MethodName, ...]
    native_high_volume_window: ExperimentsBenignCommonModeRobustnessNativeHighVolumeWindowConfig


class ExperimentsSecondaryControlledTraceGeneralizationConfig(FrozenConfigModel):
    methods: tuple[MethodName, ...]


class ExperimentsConfig(FrozenConfigModel):
    self_explanation_exclusion_validation: ExperimentsSelfExplanationExclusionValidationConfig
    pure_order_separation_validation: ExperimentsPureOrderSeparationValidationConfig
    exclusion_matched_hofd_equivalence: ExperimentsExclusionMatchedHofdEquivalenceConfig
    strong_comparator_composition_challenge: ExperimentsStrongComparatorCompositionChallengeConfig
    estimator_support_and_context_feasibility: (
        ExperimentsEstimatorSupportAndContextFeasibilityConfig
    )
    sequential_evidence_validation: ExperimentsSequentialEvidenceValidationConfig
    primary_strict_odi_evaluation: ExperimentsPrimaryStrictOdiEvaluationConfig
    exclusion_mechanism_ablation: ExperimentsExclusionMechanismAblationConfig
    purification_and_order_ablation: ExperimentsPurificationAndOrderAblationConfig
    context_and_estimator_sensitivity: ExperimentsContextAndEstimatorSensitivityConfig
    benign_common_mode_robustness: ExperimentsBenignCommonModeRobustnessConfig
    secondary_controlled_trace_generalization: (
        ExperimentsSecondaryControlledTraceGeneralizationConfig
    )


class ScalabilityTimingConfig(FrozenConfigModel):
    measured_repetitions_per_seed_client_count: ScalabilityRepetitionCount
    unmeasured_harness_warmup_epochs: EpochCount
    measured_epochs_per_repetition: PositiveEpochCount
    concurrent_experiment_cells: ConcurrentExperimentCellCount
    result_quantile: Percentile


class RuntimeConfig(FrozenConfigModel):
    automatic_technical_retries_after_initial_failure: RetryCount
    required_confirmatory_missing_cell_tolerance: MissingCellTolerance


class ArtifactsConfig(FrozenConfigModel):
    outputs_root: RelativePath
    results_root: RelativePath

    @model_validator(mode="after")
    def _validate_distinct_roots(self) -> Self:
        if self.outputs_root == self.results_root:
            raise ValueError("outputs_root and results_root must be distinct")
        return self


class ReportingPrecisionConfig(FrozenConfigModel):
    probabilities_and_rates_decimals: DecimalPlaces
    effect_sizes_decimals: DecimalPlaces
    epochs_and_minutes_decimals: DecimalPlaces
    milliseconds_and_seconds_decimals: DecimalPlaces
    adjusted_p_values_decimals: DecimalPlaces
    p_value_lower_display_threshold: Probability


class ReportingConfig(FrozenConfigModel):
    precision: ReportingPrecisionConfig


class ScientificConfig(FrozenConfigModel):
    study: StudyConfig
    time: TimeConfig
    campaign: CampaignConfig
    distributed_support: DistributedSupportConfig
    context: ContextConfig
    basis: BasisConfig
    projection: ProjectionConfig
    evidence: EvidenceConfig
    datasets: DatasetsConfig
    detectors: DetectorsConfig
    local_policy: LocalPolicyConfig
    randomness: RandomnessConfig
    synthetic: SyntheticConfig
    generators: GeneratorsConfig
    comparators: ComparatorsConfig
    numerics: NumericsConfig
    statistics: StatisticsConfig
    materiality: MaterialityConfig
    support_grids: SupportGridsConfig
    robustness: RobustnessConfig
    experiments: ExperimentsConfig
    scalability_timing: ScalabilityTimingConfig
    runtime: RuntimeConfig
    artifacts: ArtifactsConfig
    reporting: ReportingConfig


class DerivedScientificValues(FrozenConfigModel):
    model_input_dimension: FeatureDimension
    heldout_benign_is_remainder: Boolean
    local_horizon_epochs: PositiveEpochCount
    synthetic_campaign_horizon_epochs: PositiveEpochCount
    synthetic_campaign_warmup_epochs: PositiveEpochCount
    synthetic_development_seed_count: SeedCount
    synthetic_confirmatory_seed_count: SeedCount
    real_development_seed_count: SeedCount
    real_confirmatory_seed_count: SeedCount
    exact_real_sign_flip_assignment_count: SignFlipAssignmentCount
    minimum_nonoverlapping_horizons_for_zero_false_stop: MinimumNonoverlappingHorizonCount
    signed_theorem_e_sr_threshold: ESrThreshold
    signed_theorem_compensator: CompensatorValue
    histogram_edge_count: BinCount
    outside_histogram_edges: tuple[RankValue, ...]
    primary_odi_table_method_order: tuple[MethodName, ...]
    context_seed: SeedValue


class LoadedScientificConfiguration(FrozenConfigModel):
    profile: ConfigurationProfile
    source_path: ConfigSourcePath
    values: ScientificConfig
    derived: DerivedScientificValues
    material_digest: ConfigurationDigest
