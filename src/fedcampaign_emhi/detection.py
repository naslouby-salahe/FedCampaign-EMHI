import numpy as np

from fedcampaign_emhi.artifacts.records import (
    ClientDetectorScoreStream,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
    PreparedDatasetRecord,
)
from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import (
    DatasetName,
    DetectorFamily,
    DetectorFamilyRemainder,
    OperatingPointState,
    PartitionRole,
)
from fedcampaign_emhi.domain.types import (
    AutoencoderBeta,
    BatchSize,
    Boolean,
    ClientId,
    ConfidenceLevel,
    DetectorFamilyAssignment,
    DetectorScore,
    EpochCount,
    EpochIndexValue,
    FalseAlarmRate,
    FeatureFraction,
    FeatureValue,
    LearningRate,
    LocalPolicyArtifact,
    MaterialDependencyFingerprint,
    MemoryMib,
    NumericalFloor,
    NumericalTolerance,
    Probability,
    Quantile,
    RankReference,
    RankValue,
    RecordCount,
    RequiredExceedanceCount,
    SampleCap,
    SeedDerivationIdentity,
    SeedValue,
    SolverIterationLimit,
    SvmCoefficientZero,
    ThresholdValue,
    TreeCount,
    WeightDecay,
    WorkerCount,
)
from fedcampaign_emhi.emhi.structure import clip_rank, midrank
from fedcampaign_emhi.emhi.thresholds import clopper_pearson_one_sided_upper_bound
from fedcampaign_emhi.models.autoencoder import autoencoder_anomaly_scores
from fedcampaign_emhi.models.classical import (
    isolation_forest_anomaly_scores,
    one_class_svm_anomaly_scores,
)
from fedcampaign_emhi.runtime import derive_component_seed

_FAMILY_BY_REMAINDER = {
    DetectorFamilyRemainder.ISOLATION_FOREST: DetectorFamily.ISOLATION_FOREST,
    DetectorFamilyRemainder.ONE_CLASS_SVM: DetectorFamily.ONE_CLASS_SVM,
    DetectorFamilyRemainder.AUTOENCODER: DetectorFamily.AUTOENCODER,
}


def assign_detector_families(
    client_ids: tuple[ClientId, ...],
) -> tuple[DetectorFamilyAssignment, ...]:
    ordered = tuple(sorted(client_ids))
    assignments: list[DetectorFamilyAssignment] = []
    for index, client_id in enumerate(ordered):
        remainder = DetectorFamilyRemainder(index % 3)
        assignments.append(
            DetectorFamilyAssignment(
                client_id=client_id,
                zero_based_index=index,
                family=_FAMILY_BY_REMAINDER[remainder],
            )
        )
    return tuple(assignments)


def permitted_fitting_partitions() -> tuple[PartitionRole, ...]:
    return (PartitionRole.DETECTOR_FIT,)


def score_isolation_forest(
    detector_fit_rows: tuple[tuple[FeatureValue, ...], ...],
    score_rows: tuple[tuple[FeatureValue, ...], ...],
    tree_count: TreeCount,
    max_samples_cap: SampleCap,
    max_features: FeatureFraction,
    jobs: WorkerCount,
    seed: SeedValue,
) -> tuple[DetectorScore, ...]:
    return isolation_forest_anomaly_scores(
        detector_fit_rows,
        score_rows,
        tree_count,
        max_samples_cap,
        max_features,
        jobs,
        seed,
    )


def score_one_class_svm(
    detector_fit_rows: tuple[tuple[FeatureValue, ...], ...],
    score_rows: tuple[tuple[FeatureValue, ...], ...],
    nu: Probability,
    coefficient_zero: SvmCoefficientZero,
    solver_tolerance: NumericalTolerance,
    kernel_cache_mib: MemoryMib,
    max_iterations: SolverIterationLimit,
    seed: SeedValue,
) -> tuple[DetectorScore, ...]:
    return one_class_svm_anomaly_scores(
        detector_fit_rows,
        score_rows,
        nu,
        coefficient_zero,
        solver_tolerance,
        kernel_cache_mib,
        max_iterations,
        seed,
    )


def score_autoencoder(
    detector_fit_rows: tuple[tuple[FeatureValue, ...], ...],
    score_rows: tuple[tuple[FeatureValue, ...], ...],
    learning_rate: LearningRate,
    beta_one: AutoencoderBeta,
    beta_two: AutoencoderBeta,
    optimizer_epsilon: NumericalFloor,
    weight_decay: WeightDecay,
    batch_size: BatchSize,
    epoch_count: SolverIterationLimit,
    root_seed: SeedValue,
    client_id: ClientId,
) -> tuple[DetectorScore, ...]:
    return autoencoder_anomaly_scores(
        detector_fit_rows,
        score_rows,
        learning_rate,
        beta_one,
        beta_two,
        optimizer_epsilon,
        weight_decay,
        batch_size,
        epoch_count,
        root_seed,
        client_id,
    )


def family_uses_detector_fit_only(family: DetectorFamily) -> Boolean:
    return family in {
        DetectorFamily.ISOLATION_FOREST,
        DetectorFamily.ONE_CLASS_SVM,
        DetectorFamily.AUTOENCODER,
    }


def oriented_score_stream(scores: tuple[DetectorScore, ...]) -> tuple[DetectorScore, ...]:
    if not scores:
        raise ValueError("score stream must contain at least one epoch")
    return scores


def score_stream_isolation_check(score_count: RecordCount, epoch_count: RecordCount) -> None:
    if score_count != epoch_count:
        raise ValueError("detector score stream must contain exactly one score per scored epoch")


def rank_stream(
    scores: tuple[DetectorScore, ...],
    benign_reference_scores: tuple[DetectorScore, ...],
    rank_clip_epsilon: NumericalFloor,
) -> tuple[RankValue, ...]:
    if not benign_reference_scores:
        raise ValueError("marginal rank reference requires benign nuisance-fit scores")
    reference = RankReference(scores=benign_reference_scores)
    return tuple(clip_rank(midrank(score, reference), rank_clip_epsilon) for score in scores)


def detector_seed(
    root_seed: SeedValue,
    dataset_name: DatasetName,
    client_id: ClientId,
) -> SeedValue:
    return derive_component_seed(
        SeedDerivationIdentity(
            base_seed=root_seed,
            component_name="local-detector-fit",
            dataset=dataset_name,
            client_ids=(client_id,),
            coalition_ids=(),
            condition_coordinates=(),
        )
    )


def score_client(
    config: ScientificConfig,
    detector_family: DetectorFamily,
    fit_rows: tuple[tuple[FeatureValue, ...], ...],
    score_rows: tuple[tuple[FeatureValue, ...], ...],
    seed: SeedValue,
    client_id: ClientId,
) -> tuple[DetectorScore, ...]:
    if detector_family is DetectorFamily.ISOLATION_FOREST:
        detector = config.detectors.isolation_forest
        return score_isolation_forest(
            fit_rows,
            score_rows,
            detector.trees,
            detector.max_samples_cap,
            detector.max_features,
            detector.jobs,
            seed,
        )
    if detector_family is DetectorFamily.ONE_CLASS_SVM:
        detector = config.detectors.one_class_svm
        return score_one_class_svm(
            fit_rows,
            score_rows,
            detector.nu,
            detector.coefficient_zero,
            detector.solver_tolerance,
            detector.kernel_cache_mib,
            detector.max_iterations,
            seed,
        )
    detector = config.detectors.autoencoder
    if len(detector.betas) != 2:
        raise ValueError("autoencoder requires exactly two Adam beta coefficients")
    return score_autoencoder(
        fit_rows,
        score_rows,
        detector.learning_rate,
        detector.betas[0],
        detector.betas[1],
        detector.optimizer_epsilon,
        detector.weight_decay,
        detector.batch_size,
        detector.epochs,
        seed,
        client_id,
    )


def build_detector_score_artifact(
    config: ScientificConfig,
    prepared: PreparedDatasetRecord,
    split: DatasetSplitRecord,
    dataset_name: DatasetName,
    root_seed: SeedValue,
    dependency_fingerprint: MaterialDependencyFingerprint,
) -> DetectorScoreArtifactRecord:
    assignments = assign_detector_families(split.selected_client_ids)
    streams: list[ClientDetectorScoreStream] = []
    for assignment in assignments:
        client_rows = tuple(row for row in prepared.epochs if row.client_id == assignment.client_id)
        fit_rows = tuple(
            row.feature_values
            for row in client_rows
            if row.epoch_index in split.detector_fit_epochs
        )
        if not fit_rows:
            raise ValueError(
                f"selected client {assignment.client_id} has no benign detector-fit rows"
            )
        score_rows = tuple(row.feature_values for row in client_rows)
        seed = detector_seed(root_seed, dataset_name, assignment.client_id)
        scores = score_client(
            config,
            assignment.family,
            fit_rows,
            score_rows,
            seed,
            assignment.client_id,
        )
        score_stream_isolation_check(len(scores), len(client_rows))
        streams.append(
            ClientDetectorScoreStream(
                client_id=assignment.client_id,
                detector_family=assignment.family,
                detector_seed=seed,
                epoch_indexes=tuple(row.epoch_index for row in client_rows),
                scores=scores,
            )
        )
    return DetectorScoreArtifactRecord(
        dataset_name=dataset_name,
        root_seed=root_seed,
        selected_client_ids=split.selected_client_ids,
        client_streams=tuple(streams),
        dependency_fingerprint=dependency_fingerprint,
    )


def persistence_is_triggered(
    exceedances: tuple[Boolean, ...],
    required_exceedances: RequiredExceedanceCount,
    window_epochs: EpochCount,
) -> Boolean:
    if window_epochs <= 0:
        raise ValueError("window_epochs must be positive")
    examined = exceedances[-window_epochs:]
    if len(examined) < required_exceedances:
        return False
    return sum(1 for exceeded in examined if exceeded) >= required_exceedances


def score_exceeds_threshold(score: DetectorScore, threshold: ThresholdValue) -> Boolean:
    return score >= threshold


def first_local_stop_epoch(
    exceedances: tuple[Boolean, ...],
    required_exceedances: RequiredExceedanceCount,
    window_epochs: EpochCount,
) -> EpochIndexValue | None:
    for end_index in range(1, len(exceedances) + 1):
        if persistence_is_triggered(exceedances[:end_index], required_exceedances, window_epochs):
            return end_index - 1
    return None


def candidate_thresholds_from_nuisance_scores(
    nuisance_scores: tuple[DetectorScore, ...],
    quantiles: tuple[Quantile, ...],
) -> tuple[ThresholdValue, ...]:
    if not nuisance_scores:
        raise ValueError("nuisance_fit scores are required for candidate thresholds")
    array = np.asarray(nuisance_scores, dtype=np.float64)
    return tuple(float(np.quantile(array, quantile)) for quantile in quantiles)


def select_immutable_local_policy(
    candidates: tuple[LocalPolicyArtifact, ...],
    calibration_false_stop_counts: tuple[RecordCount, ...],
    horizon_count: RecordCount,
    confidence: ConfidenceLevel,
    target_pfa: FalseAlarmRate,
) -> LocalPolicyArtifact | None:
    if len(candidates) != len(calibration_false_stop_counts):
        raise ValueError("candidates and calibration_false_stop_counts must have equal length")
    ordered = sorted(
        zip(candidates, calibration_false_stop_counts, strict=True),
        key=lambda pair: (pair[0].threshold, pair[0].required_exceedances, pair[0].window_epochs),
    )
    for artifact, false_stop_count in ordered:
        upper = clopper_pearson_one_sided_upper_bound(false_stop_count, horizon_count, confidence)
        if upper <= target_pfa:
            return artifact
    return None


def heldout_false_stop_count(
    heldout_exceedance_horizons: tuple[tuple[Boolean, ...], ...],
    required_exceedances: RequiredExceedanceCount,
    window_epochs: EpochCount,
) -> RecordCount:
    stops = 0
    for horizon in heldout_exceedance_horizons:
        if first_local_stop_epoch(horizon, required_exceedances, window_epochs) is not None:
            stops += 1
    return stops


def operating_point_state_for_policy(
    artifact: LocalPolicyArtifact | None,
) -> OperatingPointState:
    if artifact is None:
        return OperatingPointState.UNAVAILABLE
    return OperatingPointState.AVAILABLE
