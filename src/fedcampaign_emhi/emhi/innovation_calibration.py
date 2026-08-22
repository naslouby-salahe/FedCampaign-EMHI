from fedcampaign_emhi.domain.types import (
    CrossFittedInnovationCalibration,
    FiniteFloat,
    FoldCount,
    ModuleContract,
    NumericalFloor,
    NumericalTolerance,
    RecordCount,
    RidgePenalty,
)
from fedcampaign_emhi.emhi.innovations import (
    center_and_scale_atom,
    projection_residual,
    sample_mean,
    sample_standard_deviation,
    unsupported_context_observation_count,
)
from fedcampaign_emhi.emhi.projection import (
    blocked_fit_is_supported,
    blocked_fold_bounds,
    fold_size_weighted_mse,
    ridge_coefficient_matrix,
    select_ridge_penalty,
)


def innovation_calibration_contract() -> ModuleContract:
    return ModuleContract(
        module_name="fedcampaign_emhi.emhi.innovation_calibration",
        ownership="blocked nuisance cross-fitting, held-fold calibration, and complete nuisance refitting",
    )


def fold_observation_indexes(
    observation_count: RecordCount, fold_count: FoldCount
) -> tuple[tuple[tuple[RecordCount, ...], tuple[RecordCount, ...]], ...]:
    bounds = blocked_fold_bounds(observation_count, fold_count)
    splits: list[tuple[tuple[RecordCount, ...], tuple[RecordCount, ...]]] = []
    all_indexes = tuple(range(observation_count))
    for start, end in bounds:
        held = tuple(range(start, end))
        training = tuple(index for index in all_indexes if index < start or index >= end)
        splits.append((training, held))
    return tuple(splits)


def select_rows(
    rows: tuple[tuple[FiniteFloat, ...], ...], indexes: tuple[RecordCount, ...]
) -> tuple[tuple[FiniteFloat, ...], ...]:
    return tuple(rows[index] for index in indexes)


def residual_mean_square(residuals: tuple[tuple[FiniteFloat, ...], ...]) -> FiniteFloat:
    if not residuals:
        raise ValueError("residual mean square requires held-fold observations")
    total = 0.0
    for residual in residuals:
        total += sum(coordinate * coordinate for coordinate in residual)
    return total / len(residuals)


def cross_validated_ridge_penalty(
    design_rows: tuple[tuple[FiniteFloat, ...], ...],
    tensors: tuple[tuple[FiniteFloat, ...], ...],
    candidates: tuple[RidgePenalty, ...],
    fold_count: FoldCount,
    tie_tolerance: NumericalTolerance,
    svd_relative_cutoff: NumericalFloor,
) -> RidgePenalty | None:
    observation_count = len(design_rows)
    if not blocked_fit_is_supported(observation_count, fold_count):
        return None
    splits = fold_observation_indexes(observation_count, fold_count)
    weighted: list[FiniteFloat] = []
    sizes = tuple(len(held) for _training, held in splits)
    for penalty in candidates:
        fold_mses: list[FiniteFloat] = []
        for training, held in splits:
            coefficients = ridge_coefficient_matrix(
                select_rows(design_rows, training),
                select_rows(tensors, training),
                penalty,
                svd_relative_cutoff,
            )
            held_residuals = tuple(
                projection_residual(tensors[index], coefficients, design_rows[index])
                for index in held
            )
            fold_mses.append(residual_mean_square(held_residuals))
        weighted.append(fold_size_weighted_mse(tuple(fold_mses), sizes))
    return select_ridge_penalty(candidates, tuple(weighted), tie_tolerance)


def held_fold_innovations(
    design_rows: tuple[tuple[FiniteFloat, ...], ...],
    tensors: tuple[tuple[FiniteFloat, ...], ...],
    fold_count: FoldCount,
    ridge_penalty: RidgePenalty,
    svd_relative_cutoff: NumericalFloor,
) -> tuple[tuple[FiniteFloat, ...], ...] | None:
    observation_count = len(design_rows)
    if not blocked_fit_is_supported(observation_count, fold_count):
        return None
    collected: list[tuple[FiniteFloat, ...]] = []
    for training, held in fold_observation_indexes(observation_count, fold_count):
        coefficients = ridge_coefficient_matrix(
            select_rows(design_rows, training),
            select_rows(tensors, training),
            ridge_penalty,
            svd_relative_cutoff,
        )
        for index in held:
            collected.append(projection_residual(tensors[index], coefficients, design_rows[index]))
    return tuple(collected)


def moments_from_held_fold_innovations(
    innovations: tuple[tuple[FiniteFloat, ...], ...],
) -> tuple[tuple[FiniteFloat, ...], tuple[FiniteFloat, ...]] | None:
    if unsupported_context_observation_count(len(innovations)):
        return None
    dimension = len(innovations[0])
    means: list[FiniteFloat] = []
    deviations: list[FiniteFloat] = []
    for coordinate_index in range(dimension):
        series = tuple(innovation[coordinate_index] for innovation in innovations)
        means.append(sample_mean(series))
        deviations.append(sample_standard_deviation(series))
    return tuple(means), tuple(deviations)


def calibrate_innovations_on_nuisance_fit(
    design_rows: tuple[tuple[FiniteFloat, ...], ...],
    tensors: tuple[tuple[FiniteFloat, ...], ...],
    candidates: tuple[RidgePenalty, ...],
    fold_count: FoldCount,
    tie_tolerance: NumericalTolerance,
    svd_relative_cutoff: NumericalFloor,
    scale_floor: NumericalFloor,
) -> CrossFittedInnovationCalibration | None:
    if len(design_rows) != len(tensors):
        raise ValueError("design_rows and tensors must be aligned")
    selected = cross_validated_ridge_penalty(
        design_rows, tensors, candidates, fold_count, tie_tolerance, svd_relative_cutoff
    )
    if selected is None:
        return None
    innovations = held_fold_innovations(
        design_rows, tensors, fold_count, selected, svd_relative_cutoff
    )
    if innovations is None:
        return None
    moments = moments_from_held_fold_innovations(innovations)
    if moments is None:
        return None
    means, deviations = moments
    complete_coefficients = ridge_coefficient_matrix(
        design_rows, tensors, selected, svd_relative_cutoff
    )
    standardized = tuple(
        center_and_scale_atom(atom, means, deviations, scale_floor) for atom in innovations
    )
    return CrossFittedInnovationCalibration(
        held_fold_innovations=innovations,
        coordinate_means=means,
        coordinate_deviations=deviations,
        standardized_held_fold_innovations=standardized,
        complete_nuisance_coefficients=complete_coefficients,
        selected_ridge_penalty=selected,
    )
