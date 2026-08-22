import numpy as np
from sklearn.svm import OneClassSVM

from fedcampaign_emhi.domain.types import (
    FiniteFloat,
    MemoryMib,
    NumericalTolerance,
    Probability,
    SeedValue,
    SolverIterationLimit,
)


def one_class_svm_anomaly_scores(
    fit_rows: tuple[tuple[FiniteFloat, ...], ...],
    score_rows: tuple[tuple[FiniteFloat, ...], ...],
    nu: Probability,
    coefficient_zero: FiniteFloat,
    solver_tolerance: NumericalTolerance,
    kernel_cache_mib: MemoryMib,
    max_iterations: SolverIterationLimit,
    seed: SeedValue,
) -> tuple[FiniteFloat, ...]:
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
    oriented: list[FiniteFloat] = []
    for index in range(int(scored.reshape(-1).shape[0])):
        oriented.append(-float(scored.reshape(-1)[index]))
    return tuple(oriented)
