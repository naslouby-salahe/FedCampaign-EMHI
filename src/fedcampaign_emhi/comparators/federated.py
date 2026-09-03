import numpy as np
from numpy.typing import NDArray

from fedcampaign_emhi.domain.types import (
    AutoencoderBeta,
    BatchSize,
    ClientId,
    FeatureValue,
    LearningRate,
    NumericalFloor,
    Probability,
    RecordCount,
    SeedCoordinate,
    SeedDerivationIdentity,
    SeedValue,
    SolverIterationLimit,
    WeightDecay,
)
from fedcampaign_emhi.models.autoencoder import (
    FittedAutoencoder,
    initial_xavier_autoencoder_parameters,
    train_client_autoencoder_epochs,
)
from fedcampaign_emhi.runtime import derive_component_seed, thirty_two_bit_seed


def fedavg_participant_indexes(
    client_count: RecordCount,
    participation_count: RecordCount,
    root_seed: SeedValue,
    client_ids: tuple[ClientId, ...],
    round_index: SolverIterationLimit,
) -> tuple[RecordCount, ...]:
    selection_seed = derive_component_seed(
        SeedDerivationIdentity(
            base_seed=root_seed,
            component_name="fedavg_autoencoder_participation",
            dataset=None,
            client_ids=client_ids,
            coalition_ids=(),
            condition_coordinates=(SeedCoordinate(name="round_index", scalar=round_index),),
        )
    )
    participation_order = np.random.default_rng(thirty_two_bit_seed(selection_seed)).permutation(
        client_count
    )
    return tuple(sorted(int(index) for index in participation_order[:participation_count]))


def fedavg_sample_weighted_layer_mean(
    layer_values: tuple[NDArray[np.float32], ...],
    sample_counts: tuple[RecordCount, ...],
) -> NDArray[np.float32]:
    if not layer_values or len(layer_values) != len(sample_counts):
        raise ValueError("FedAvg aggregation requires aligned client layer values and counts")
    total_samples = float(sum(sample_counts))
    if total_samples <= 0.0:
        raise ValueError("FedAvg aggregation requires positive total sample count")
    accumulated = np.sum(
        np.stack(
            [
                value.astype(np.float64) * count
                for value, count in zip(layer_values, sample_counts, strict=True)
            ]
        ),
        axis=0,
    )
    return (accumulated / total_samples).astype(np.float32)


def fit_federated_autoencoder(
    client_fit_rows: tuple[tuple[tuple[FeatureValue, ...], ...], ...],
    client_ids: tuple[ClientId, ...],
    rounds: SolverIterationLimit,
    local_epochs_per_round: SolverIterationLimit,
    client_participation_fraction: Probability,
    learning_rate: LearningRate,
    beta_one: AutoencoderBeta,
    beta_two: AutoencoderBeta,
    optimizer_epsilon: NumericalFloor,
    weight_decay: WeightDecay,
    batch_size: BatchSize,
    root_seed: SeedValue,
) -> FittedAutoencoder:
    if not client_fit_rows or len(client_fit_rows) != len(client_ids):
        raise ValueError("FedAvg autoencoder requires aligned per-client detector-fit rows")
    client_matrices = tuple(np.asarray(rows, dtype=np.float32) for rows in client_fit_rows)
    for matrix in client_matrices:
        if matrix.shape[0] == 0:
            raise ValueError("FedAvg autoencoder requires non-empty per-client detector-fit rows")
    input_dimension = int(client_matrices[0].shape[1])
    global_weights, global_biases = initial_xavier_autoencoder_parameters(
        input_dimension, root_seed
    )
    participation_count = max(1, round(client_participation_fraction * len(client_ids)))
    for round_index in range(rounds):
        participating_indexes = fedavg_participant_indexes(
            len(client_ids), participation_count, root_seed, client_ids, round_index
        )
        round_weights: list[tuple[NDArray[np.float32], ...]] = []
        round_biases: list[tuple[NDArray[np.float32], ...]] = []
        round_sample_counts: list[RecordCount] = []
        for client_index in participating_indexes:
            client_weights, client_biases = train_client_autoencoder_epochs(
                client_matrices[client_index],
                global_weights,
                global_biases,
                learning_rate,
                beta_one,
                beta_two,
                optimizer_epsilon,
                weight_decay,
                batch_size,
                local_epochs_per_round,
                root_seed,
                client_ids[client_index],
                round_index * local_epochs_per_round,
            )
            round_weights.append(client_weights)
            round_biases.append(client_biases)
            round_sample_counts.append(int(client_matrices[client_index].shape[0]))
        sample_counts = tuple(round_sample_counts)
        global_weights = tuple(
            fedavg_sample_weighted_layer_mean(
                tuple(weights[layer_index] for weights in round_weights), sample_counts
            )
            for layer_index in range(len(global_weights))
        )
        global_biases = tuple(
            fedavg_sample_weighted_layer_mean(
                tuple(biases[layer_index] for biases in round_biases), sample_counts
            )
            for layer_index in range(len(global_biases))
        )
    return FittedAutoencoder(global_weights, global_biases)
