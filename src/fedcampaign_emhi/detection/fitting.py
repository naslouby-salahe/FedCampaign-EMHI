from fedcampaign_emhi.domain.enums import DetectorFamily, PartitionRole
from fedcampaign_emhi.domain.types import (
    BatchSize,
    ClientId,
    FeatureFraction,
    FiniteFloat,
    LearningRate,
    MemoryMib,
    NumericalTolerance,
    Probability,
    SampleCap,
    SeedValue,
    SolverIterationLimit,
    TreeCount,
    WorkerCount,
)
from fedcampaign_emhi.models.autoencoder import autoencoder_anomaly_scores
from fedcampaign_emhi.models.isolation_forest import isolation_forest_anomaly_scores
from fedcampaign_emhi.models.one_class_svm import one_class_svm_anomaly_scores


def permitted_fitting_partitions() -> tuple[PartitionRole, ...]:
    return (PartitionRole.DETECTOR_FIT,)


def score_isolation_forest(
    detector_fit_rows: tuple[tuple[FiniteFloat, ...], ...],
    score_rows: tuple[tuple[FiniteFloat, ...], ...],
    tree_count: TreeCount,
    max_samples_cap: SampleCap,
    max_features: FeatureFraction,
    jobs: WorkerCount,
    seed: SeedValue,
) -> tuple[FiniteFloat, ...]:
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
    detector_fit_rows: tuple[tuple[FiniteFloat, ...], ...],
    score_rows: tuple[tuple[FiniteFloat, ...], ...],
    nu: Probability,
    coefficient_zero: FiniteFloat,
    solver_tolerance: NumericalTolerance,
    kernel_cache_mib: MemoryMib,
    max_iterations: SolverIterationLimit,
    seed: SeedValue,
) -> tuple[FiniteFloat, ...]:
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
    detector_fit_rows: tuple[tuple[FiniteFloat, ...], ...],
    score_rows: tuple[tuple[FiniteFloat, ...], ...],
    learning_rate: LearningRate,
    beta_one: FiniteFloat,
    beta_two: FiniteFloat,
    optimizer_epsilon: FiniteFloat,
    weight_decay: FiniteFloat,
    batch_size: BatchSize,
    epoch_count: SolverIterationLimit,
    root_seed: SeedValue,
    client_id: ClientId,
) -> tuple[FiniteFloat, ...]:
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


def family_uses_detector_fit_only(family: DetectorFamily) -> bool:
    return family in {
        DetectorFamily.ISOLATION_FOREST,
        DetectorFamily.ONE_CLASS_SVM,
        DetectorFamily.AUTOENCODER,
    }
