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
from fedcampaign_emhi.runtime import log_stage, thirty_two_bit_seed


class FittedIsolationForest:
    __slots__ = ("_estimator",)

    def __init__(self, estimator: IsolationForest) -> None:
        self._estimator = estimator

    def score(self, score_rows: tuple[tuple[FeatureValue, ...], ...]) -> tuple[AnomalyScore, ...]:
        score_matrix = np.asarray(score_rows, dtype=np.float64)
        scored = np.array(self._estimator.score_samples(score_matrix), dtype=np.float64)
        return tuple((-scored).tolist())


@log_stage("models.classical")
def fit_isolation_forest(
    fit_rows: tuple[tuple[FeatureValue, ...], ...],
    tree_count: TreeCount,
    max_samples_cap: SampleCap,
    max_features: FeatureFraction,
    jobs: WorkerCount,
    seed: SeedValue,
) -> FittedIsolationForest:
    if not fit_rows:
        raise ValueError("Isolation Forest requires a non-empty detector-fit matrix")
    fit_matrix = np.asarray(fit_rows, dtype=np.float64)
    max_samples = min(max_samples_cap, int(fit_matrix.shape[0]))
    model = IsolationForest(random_state=thirty_two_bit_seed(seed))
    model.set_params(
        n_estimators=tree_count,
        max_samples=max_samples,
        max_features=max_features,
        n_jobs=jobs,
        bootstrap=False,
        contamination="auto",
        warm_start=False,
        verbose=0,
    )
    model.fit(fit_matrix)
    return FittedIsolationForest(model)


def isolation_forest_anomaly_scores(
    fit_rows: tuple[tuple[FeatureValue, ...], ...],
    score_rows: tuple[tuple[FeatureValue, ...], ...],
    tree_count: TreeCount,
    max_samples_cap: SampleCap,
    max_features: FeatureFraction,
    jobs: WorkerCount,
    seed: SeedValue,
) -> tuple[AnomalyScore, ...]:
    fitted = fit_isolation_forest(fit_rows, tree_count, max_samples_cap, max_features, jobs, seed)
    return fitted.score(score_rows)


class FittedOneClassSvm:
    __slots__ = ("_estimator",)

    def __init__(self, estimator: OneClassSVM) -> None:
        self._estimator = estimator

    def score(self, score_rows: tuple[tuple[FeatureValue, ...], ...]) -> tuple[AnomalyScore, ...]:
        score_matrix = np.asarray(score_rows, dtype=np.float64)
        scored = np.array(self._estimator.decision_function(score_matrix), dtype=np.float64)
        return tuple((-scored).tolist())


@log_stage("models.classical")
def fit_one_class_svm(
    fit_rows: tuple[tuple[FeatureValue, ...], ...],
    nu: Probability,
    coefficient_zero: SvmCoefficientZero,
    solver_tolerance: NumericalTolerance,
    kernel_cache_mib: MemoryMib,
    max_iterations: SolverIterationLimit,
    seed: SeedValue,
) -> FittedOneClassSvm:
    if not fit_rows:
        raise ValueError("One-Class SVM requires a non-empty detector-fit matrix")
    del seed
    fit_matrix = np.asarray(fit_rows, dtype=np.float64)
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
    return FittedOneClassSvm(model)


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
    fitted = fit_one_class_svm(
        fit_rows,
        nu,
        coefficient_zero,
        solver_tolerance,
        kernel_cache_mib,
        max_iterations,
        seed,
    )
    return fitted.score(score_rows)
