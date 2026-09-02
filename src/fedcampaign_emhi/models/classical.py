import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM

from fedcampaign_emhi.domain.types import (
    AnomalyScore,
    FeatureFraction,
    FeatureValue,
    MemoryMib,
    NumericalTolerance,
    Probability,
    SampleCap,
    SeedValue,
    SolverIterationLimit,
    SvmCoefficientZero,
    TreeCount,
    WorkerCount,
)
from fedcampaign_emhi.runtime import thirty_two_bit_seed


def isolation_forest_anomaly_scores(
    fit_rows: tuple[tuple[FeatureValue, ...], ...],
    score_rows: tuple[tuple[FeatureValue, ...], ...],
    tree_count: TreeCount,
    max_samples_cap: SampleCap,
    max_features: FeatureFraction,
    jobs: WorkerCount,
    seed: SeedValue,
) -> tuple[AnomalyScore, ...]:
    if not fit_rows:
        raise ValueError("Isolation Forest requires a non-empty detector-fit matrix")
    fit_matrix = np.asarray(fit_rows, dtype=np.float64)
    score_matrix = np.asarray(score_rows, dtype=np.float64)
    max_samples = min(int(max_samples_cap), int(fit_matrix.shape[0]))
    model = IsolationForest(random_state=int(thirty_two_bit_seed(seed)))
    model.set_params(
        n_estimators=int(tree_count),
        max_samples=max_samples,
        max_features=float(max_features),
        n_jobs=int(jobs),
        bootstrap=False,
        contamination="auto",
        warm_start=False,
        verbose=0,
    )
    model.fit(fit_matrix)
    scored = np.array(model.score_samples(score_matrix), dtype=np.float64)
    return tuple((-scored).tolist())


def one_class_svm_anomaly_scores(
    fit_rows: tuple[tuple[FeatureValue, ...], ...],
    score_rows: tuple[tuple[FeatureValue, ...], ...],
    nu: Probability,
    coefficient_zero: SvmCoefficientZero,
    solver_tolerance: NumericalTolerance,
    kernel_cache_mib: MemoryMib,
    max_iterations: SolverIterationLimit,
    seed: SeedValue,
) -> tuple[AnomalyScore, ...]:
    if not fit_rows:
        raise ValueError("One-Class SVM requires a non-empty detector-fit matrix")
    del seed
    fit_matrix = np.asarray(fit_rows, dtype=np.float64)
    score_matrix = np.asarray(score_rows, dtype=np.float64)
    model = OneClassSVM(
        kernel="rbf",
        nu=nu,
        gamma="scale",
        coef0=coefficient_zero,
        tol=solver_tolerance,
        cache_size=kernel_cache_mib,
        max_iter=max_iterations,
        shrinking=True,
        verbose=False,
    )
    model.fit(fit_matrix)
    scored = np.array(model.decision_function(score_matrix), dtype=np.float64)
    return tuple((-scored).tolist())
