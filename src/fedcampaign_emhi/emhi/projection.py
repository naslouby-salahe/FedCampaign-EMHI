from dataclasses import dataclass

import numpy as np

from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import (
    BasisCoordinate,
    BasisSize,
    Boolean,
    DesignColumnCount,
    EpochIndexValue,
    FoldCount,
    GramConditionNumber,
    NuisanceCoefficient,
    NumericalFloor,
    NumericalTolerance,
    ProjectionMeanSquaredError,
    RankValue,
    RecordCount,
    RidgePenalty,
    TensorDimension,
)
from fedcampaign_emhi.emhi.structure import bounded_basis, tensor_representation


@dataclass(frozen=True)
class ProperSubsetDesignShape:
    design_column_count: DesignColumnCount
    tensor_dimension: TensorDimension


def proper_subset_design_column_count(
    coalition_order: CoalitionOrder, basis_size: BasisSize
) -> DesignColumnCount:
    if coalition_order is CoalitionOrder.ONE:
        return 1
    if coalition_order is CoalitionOrder.TWO:
        return 1 + (2 * basis_size)
    return 1 + (3 * basis_size) + (3 * (basis_size**2))


def proper_subset_design_shape(
    coalition_order: CoalitionOrder, basis_size: BasisSize
) -> ProperSubsetDesignShape:
    return ProperSubsetDesignShape(
        design_column_count=proper_subset_design_column_count(coalition_order, basis_size),
        tensor_dimension=basis_size ** int(coalition_order),
    )


def proper_subset_design_row(
    member_ranks: tuple[RankValue, ...], basis_size: BasisSize
) -> tuple[BasisCoordinate, ...]:
    order = len(member_ranks)
    if order < 1:
        raise ValueError("proper-subset design requires at least one coalition member")
    expected = proper_subset_design_shape(CoalitionOrder(order), basis_size)
    intercept = (1.0,)
    if order == 1:
        if len(intercept) != expected.design_column_count:
            raise ValueError("order-one proper-subset design shape mismatch")
        return intercept
    singletons: list[BasisCoordinate] = []
    for rank in member_ranks:
        singletons.extend(bounded_basis(rank, basis_size))
    if order == 2:
        row = intercept + tuple(singletons)
        if len(row) != expected.design_column_count:
            raise ValueError("order-two proper-subset design shape mismatch")
        return row
    pair_coordinates: list[BasisCoordinate] = []
    for left_index in range(order):
        for right_index in range(left_index + 1, order):
            pair_coordinates.extend(
                tensor_representation(
                    (member_ranks[left_index], member_ranks[right_index]), basis_size
                )
            )
    row = intercept + tuple(singletons) + tuple(pair_coordinates)
    if len(row) != expected.design_column_count:
        raise ValueError("proper-subset design shape mismatch")
    return row


def blocked_fit_is_supported(observation_count: RecordCount, fold_count: FoldCount) -> Boolean:
    return observation_count >= fold_count


def blocked_fold_bounds(
    observation_count: RecordCount, fold_count: FoldCount
) -> tuple[tuple[EpochIndexValue, EpochIndexValue], ...]:
    if observation_count < fold_count:
        raise ValueError("requested fit is unsupported because n is less than k")
    quotient, remainder = divmod(observation_count, fold_count)
    bounds: list[tuple[EpochIndexValue, EpochIndexValue]] = []
    start = 0
    for fold_index in range(fold_count):
        size = quotient + 1 if fold_index < remainder else quotient
        end = start + size
        bounds.append((start, end))
        start = end
    return tuple(bounds)


def blocked_fold_sizes(
    observation_count: RecordCount, fold_count: FoldCount
) -> tuple[RecordCount, ...]:
    return tuple(end - start for start, end in blocked_fold_bounds(observation_count, fold_count))


def fold_size_weighted_mse(
    fold_mses: tuple[ProjectionMeanSquaredError, ...], fold_sizes: tuple[RecordCount, ...]
) -> ProjectionMeanSquaredError:
    if len(fold_mses) != len(fold_sizes):
        raise ValueError("fold_mses and fold_sizes must have equal length")
    total = sum(fold_sizes)
    if total <= 0:
        raise ValueError("fold sizes must be positive in aggregate")
    return sum(mse * size for mse, size in zip(fold_mses, fold_sizes, strict=True)) / total


def select_ridge_penalty(
    candidates: tuple[RidgePenalty, ...],
    weighted_mses: tuple[ProjectionMeanSquaredError, ...],
    tie_tolerance: NumericalTolerance,
) -> RidgePenalty:
    if not candidates or len(candidates) != len(weighted_mses):
        raise ValueError("candidates and weighted_mses must be non-empty and aligned")
    selected = candidates[0]
    selected_mse = weighted_mses[0]
    for penalty, mse in list(zip(candidates, weighted_mses, strict=True))[1:]:
        if mse + tie_tolerance < selected_mse:
            selected = penalty
            selected_mse = mse
            continue
        if abs(mse - selected_mse) <= tie_tolerance and penalty > selected:
            selected = penalty
            selected_mse = min(selected_mse, mse)
    return selected


def unregularized_gram_condition_number(
    design_columns: tuple[tuple[BasisCoordinate, ...], ...],
) -> GramConditionNumber:
    matrix = np.asarray(design_columns, dtype=np.float64)
    if matrix.ndim != 2:
        raise ValueError("design_columns must be a two-dimensional array")
    variances = np.var(matrix, axis=0)
    kept = matrix[:, variances > 0.0]
    if kept.size == 0:
        raise ValueError("design has no non-constant columns")
    gram = kept.T @ kept
    singular_values = np.linalg.svd(gram, compute_uv=False)
    smallest = float(np.min(singular_values))
    if smallest <= 0.0:
        raise ValueError("unregularized Gram matrix is singular")
    return float(np.max(singular_values) / smallest)


def ridge_coefficient_matrix(
    design_columns: tuple[tuple[BasisCoordinate, ...], ...],
    responses: tuple[tuple[BasisCoordinate, ...], ...],
    ridge_penalty: RidgePenalty,
    svd_relative_cutoff: NumericalFloor,
) -> tuple[tuple[NuisanceCoefficient, ...], ...]:
    design = np.asarray(design_columns, dtype=np.float64)
    target = np.asarray(responses, dtype=np.float64)
    if design.ndim != 2 or target.ndim != 2:
        raise ValueError("design and responses must be two-dimensional")
    if design.shape[0] != target.shape[0]:
        raise ValueError("design and responses must contain the same observation count")
    penalty = np.zeros((design.shape[1], design.shape[1]), dtype=np.float64)
    if design.shape[1] > 1:
        penalty[1:, 1:] = np.eye(design.shape[1] - 1, dtype=np.float64) * ridge_penalty
    gram = design.T @ design
    if ridge_penalty <= 0.0:
        coefficients = np.linalg.pinv(design, rcond=svd_relative_cutoff) @ target
    else:
        coefficients = np.linalg.solve(gram + penalty, design.T @ target)
    return tuple(tuple(float(value) for value in row) for row in coefficients)
