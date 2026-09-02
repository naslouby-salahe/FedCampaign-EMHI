import statistics

from fedcampaign_emhi.domain.types import (
    BasisCoordinate,
    Boolean,
    InnovationCoordinate,
    InnovationDeviation,
    InnovationMean,
    NuisanceCoefficient,
    NumericalFloor,
    RecordCount,
    StandardizedAtomCoordinate,
)


def sample_mean(values: tuple[InnovationCoordinate, ...]) -> InnovationMean:
    if not values:
        raise ValueError("mean requires at least one observation")
    return statistics.fmean(values)


def sample_standard_deviation(values: tuple[InnovationCoordinate, ...]) -> InnovationDeviation:
    if len(values) < 2:
        raise ValueError("sample standard deviation requires at least two observations")
    return statistics.stdev(values)


def centered_scaled_coordinate(
    coordinate: InnovationCoordinate,
    mean: InnovationMean,
    deviation: InnovationDeviation,
    scale_floor: NumericalFloor,
) -> StandardizedAtomCoordinate:
    scale = max(deviation, scale_floor)
    return (coordinate - mean) / scale


def center_and_scale_atom(
    atom: tuple[InnovationCoordinate, ...],
    means: tuple[InnovationMean, ...],
    deviations: tuple[InnovationDeviation, ...],
    scale_floor: NumericalFloor,
) -> tuple[StandardizedAtomCoordinate, ...]:
    if len(atom) != len(means) or len(atom) != len(deviations):
        raise ValueError("atom, means, and deviations must be aligned")
    return tuple(
        centered_scaled_coordinate(coordinate, mean, deviation, scale_floor)
        for coordinate, mean, deviation in zip(atom, means, deviations, strict=True)
    )


def innovation_excludes_same_order_representation(
    tensor: tuple[InnovationCoordinate, ...],
    coefficients: tuple[tuple[NuisanceCoefficient, ...], ...],
    design_row: tuple[BasisCoordinate, ...],
) -> tuple[InnovationCoordinate, ...]:
    if len(coefficients) != len(design_row):
        raise ValueError("coefficient rows must match design columns")
    predicted: list[InnovationCoordinate] = []
    dimension = len(tensor)
    for coordinate_index in range(dimension):
        total = 0.0
        for column_index, design_value in enumerate(design_row):
            total += coefficients[column_index][coordinate_index] * design_value
        predicted.append(total)
    return tuple(left - right for left, right in zip(tensor, predicted, strict=True))


def projection_residual(
    tensor: tuple[InnovationCoordinate, ...],
    coefficients: tuple[tuple[NuisanceCoefficient, ...], ...],
    design_row: tuple[BasisCoordinate, ...],
) -> tuple[InnovationCoordinate, ...]:
    return innovation_excludes_same_order_representation(tensor, coefficients, design_row)


def unsupported_context_observation_count(observation_count: RecordCount) -> Boolean:
    return observation_count < 2
