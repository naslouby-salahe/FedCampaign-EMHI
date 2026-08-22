import numpy as np
from numpy.typing import NDArray
from sklearn.ensemble import IsolationForest

from fedcampaign_emhi.domain.types import (
    FeatureFraction,
    FiniteFloat,
    SampleCap,
    SeedValue,
    TreeCount,
    WorkerCount,
)
from fedcampaign_emhi.runtime.determinism import thirty_two_bit_seed


def _float64_row(values: NDArray[np.float64]) -> tuple[FiniteFloat, ...]:
    array = np.array(values, dtype=np.float64).reshape(-1)
    oriented: list[FiniteFloat] = []
    for index in range(int(array.shape[0])):
        oriented.append(float(array[index]))
    return tuple(oriented)


def isolation_forest_anomaly_scores(
    fit_rows: tuple[tuple[FiniteFloat, ...], ...],
    score_rows: tuple[tuple[FiniteFloat, ...], ...],
    tree_count: TreeCount,
    max_samples_cap: SampleCap,
    max_features: FeatureFraction,
    jobs: WorkerCount,
    seed: SeedValue,
) -> tuple[FiniteFloat, ...]:
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
    raw_scores = _float64_row(scored)
    return tuple(-score for score in raw_scores)
