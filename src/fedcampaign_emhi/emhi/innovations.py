from math import sqrt

from fedcampaign_emhi.domain.types import FiniteFloat, NumericalFloor, RecordCount


def sample_mean(values: tuple[FiniteFloat, ...]) -> FiniteFloat:
    if not values:
        raise ValueError("mean requires at least one observation")
    return sum(values) / len(values)


def sample_standard_deviation(values: tuple[FiniteFloat, ...]) -> FiniteFloat:
    count = len(values)
    if count < 2:
        raise ValueError("sample standard deviation requires at least two observations")
    mean = sample_mean(values)
    squared = sum((value - mean) ** 2 for value in values)
    return sqrt(squared / (count - 1))


def centered_scaled_coordinate(
    coordinate: FiniteFloat,
    mean: FiniteFloat,
    deviation: FiniteFloat,
    scale_floor: NumericalFloor,
) -> FiniteFloat:
    scale = max(deviation, scale_floor)
    return (coordinate - mean) / scale


def center_and_scale_atom(
    atom: tuple[FiniteFloat, ...],
    means: tuple[FiniteFloat, ...],
    deviations: tuple[FiniteFloat, ...],
    scale_floor: NumericalFloor,
) -> tuple[FiniteFloat, ...]:
    if len(atom) != len(means) or len(atom) != len(deviations):
        raise ValueError("atom, means, and deviations must be aligned")
    return tuple(
        centered_scaled_coordinate(coordinate, mean, deviation, scale_floor)
        for coordinate, mean, deviation in zip(atom, means, deviations, strict=True)
    )


def projection_residual(
    tensor: tuple[FiniteFloat, ...],
    coefficients: tuple[tuple[FiniteFloat, ...], ...],
    design_row: tuple[FiniteFloat, ...],
) -> tuple[FiniteFloat, ...]:
    if len(coefficients) != len(design_row):
        raise ValueError("coefficient rows must match design columns")
    predicted: list[FiniteFloat] = []
    dimension = len(tensor)
    for coordinate_index in range(dimension):
        total = 0.0
        for column_index, design_value in enumerate(design_row):
            total += coefficients[column_index][coordinate_index] * design_value
        predicted.append(total)
    return tuple(left - right for left, right in zip(tensor, predicted, strict=True))


def unsupported_context_observation_count(observation_count: RecordCount) -> bool:
    return observation_count < 2


def innovation_excludes_same_order_representation(
    tensor: tuple[FiniteFloat, ...],
    coefficients: tuple[tuple[FiniteFloat, ...], ...],
    design_row: tuple[FiniteFloat, ...],
) -> tuple[FiniteFloat, ...]:
    return projection_residual(tensor, coefficients, design_row)
