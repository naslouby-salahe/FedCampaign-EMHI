import numpy as np

from fedcampaign_emhi.domain.types import FiniteFloat, PositiveInt, Probability


def selected_factor_rank(
    singular_values: tuple[FiniteFloat, ...],
    cumulative_variance_target: Probability,
    fallback_rank: PositiveInt,
    candidate_ranks: tuple[PositiveInt, ...],
) -> PositiveInt:
    total = sum(value * value for value in singular_values)
    if total <= 0.0:
        return fallback_rank
    cumulative = 0.0
    for rank, value in enumerate(singular_values, start=1):
        cumulative += (value * value) / total
        if rank in candidate_ranks and cumulative >= cumulative_variance_target:
            return rank
    if fallback_rank in candidate_ranks:
        return fallback_rank
    return candidate_ranks[-1]


def global_factor_residual_scores(
    rank_matrix: tuple[tuple[FiniteFloat, ...], ...],
    factor_rank: PositiveInt,
) -> tuple[FiniteFloat, ...]:
    matrix = np.asarray(rank_matrix, dtype=np.float64)
    if matrix.ndim != 2:
        raise ValueError("rank_matrix must be two-dimensional")
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    _left, _singular, right = np.linalg.svd(centered, full_matrices=False)
    factors = right[:factor_rank].T
    reconstruction = centered @ factors @ factors.T
    residual = centered - reconstruction
    norms = np.linalg.norm(residual, axis=1)
    return tuple(float(norm) for norm in norms)
