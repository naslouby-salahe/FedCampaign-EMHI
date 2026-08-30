import numpy as np
from numpy.typing import NDArray

from fedcampaign_emhi.domain.types import (
    Boolean,
    FeatureDimension,
    FiniteFloat,
    LayerWidth,
    RecordCount,
)
from fedcampaign_emhi.models.autoencoder import autoencoder_layer_widths


def fedavg_weighted_mean(
    client_parameters: tuple[tuple[FiniteFloat, ...], ...],
    sample_counts: tuple[RecordCount, ...],
) -> tuple[FiniteFloat, ...]:
    if not client_parameters or len(client_parameters) != len(sample_counts):
        raise ValueError("FedAvg requires aligned client parameters and sample counts")
    total = sum(sample_counts)
    if total <= 0:
        raise ValueError("FedAvg sample counts must be positive in aggregate")
    accumulator = np.zeros(len(client_parameters[0]), dtype=np.float64)
    for parameters, count in zip(client_parameters, sample_counts, strict=True):
        accumulator += np.asarray(parameters, dtype=np.float64) * count
    averaged = accumulator / total
    return tuple(float(coordinate) for coordinate in averaged.tolist())


def store_parameters_float32(parameters: tuple[FiniteFloat, ...]) -> tuple[FiniteFloat, ...]:
    stored: NDArray[np.float32] = np.asarray(parameters, dtype=np.float32)
    return tuple(float(coordinate) for coordinate in stored.tolist())


def optimizer_state_resets_each_round() -> Boolean:
    return True


def federated_autoencoder_widths(
    input_dimension: FeatureDimension,
) -> tuple[FeatureDimension, LayerWidth, LayerWidth, LayerWidth, FeatureDimension]:
    return autoencoder_layer_widths(input_dimension)
