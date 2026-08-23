import math

import numpy as np
from numpy.typing import NDArray

from fedcampaign_emhi.domain.types import (
    BatchSize,
    ClientId,
    FeatureDimension,
    FiniteFloat,
    LayerWidth,
    LearningRate,
    SeedCoordinate,
    SeedDerivationIdentity,
    SeedValue,
    SolverIterationLimit,
)
from fedcampaign_emhi.runtime.determinism import derive_component_seed, thirty_two_bit_seed

AUTOENCODER_ENCODER_WIDTH: LayerWidth = 32
AUTOENCODER_LATENT_WIDTH: LayerWidth = 8
AUTOENCODER_DECODER_WIDTH: LayerWidth = 32
RELU_XAVIER_GAIN = math.sqrt(2.0)
OUTPUT_XAVIER_GAIN = 1.0


def autoencoder_layer_widths(
    input_dimension: FeatureDimension,
) -> tuple[FeatureDimension, LayerWidth, LayerWidth, LayerWidth, FeatureDimension]:
    return (
        input_dimension,
        AUTOENCODER_ENCODER_WIDTH,
        AUTOENCODER_LATENT_WIDTH,
        AUTOENCODER_DECODER_WIDTH,
        input_dimension,
    )


def batch_permutation_seed(
    root_seed: SeedValue, client_id: ClientId, training_epoch: SolverIterationLimit
) -> SeedValue:
    identity = SeedDerivationIdentity(
        base_seed=root_seed,
        component_name="autoencoder_batch_permutation",
        dataset=None,
        client_ids=(client_id,),
        coalition_ids=(),
        condition_coordinates=(SeedCoordinate(name="training_epoch", scalar=training_epoch),),
    )
    return derive_component_seed(identity)


def _xavier_uniform(
    generator: np.random.Generator,
    fan_in: FeatureDimension,
    fan_out: FeatureDimension,
    gain: FiniteFloat,
) -> NDArray[np.float32]:
    bound = gain * math.sqrt(6.0 / (fan_in + fan_out))
    return generator.uniform(-bound, bound, size=(fan_in, fan_out)).astype(np.float32)


def _relu(values: NDArray[np.float32]) -> NDArray[np.float32]:
    return np.maximum(values, 0.0, dtype=np.float32)


def autoencoder_anomaly_scores(
    fit_rows: tuple[tuple[FiniteFloat, ...], ...],
    score_rows: tuple[tuple[FiniteFloat, ...], ...],
    learning_rate: LearningRate,
    beta_one: FiniteFloat,
    beta_two: FiniteFloat,
    optimizer_epsilon: FiniteFloat,
    weight_decay: FiniteFloat,
    batch_size: BatchSize,
    epoch_count: SolverIterationLimit,
    root_seed: SeedValue,
    client_id: ClientId,
) -> tuple[FiniteFloat, ...]:
    if not fit_rows:
        raise ValueError("autoencoder requires a non-empty detector-fit matrix")
    fit_matrix = np.asarray(fit_rows, dtype=np.float32)
    score_matrix = np.asarray(score_rows, dtype=np.float32)
    input_dimension = int(fit_matrix.shape[1])
    widths = autoencoder_layer_widths(input_dimension)
    init_generator = np.random.default_rng(thirty_two_bit_seed(root_seed))
    weights = (
        _xavier_uniform(init_generator, widths[0], widths[1], RELU_XAVIER_GAIN),
        _xavier_uniform(init_generator, widths[1], widths[2], RELU_XAVIER_GAIN),
        _xavier_uniform(init_generator, widths[2], widths[3], RELU_XAVIER_GAIN),
        _xavier_uniform(init_generator, widths[3], widths[4], OUTPUT_XAVIER_GAIN),
    )
    biases = tuple(np.zeros((width,), dtype=np.float32) for width in widths[1:])
    first_moments = tuple(np.zeros_like(weight) for weight in weights)
    second_moments = tuple(np.zeros_like(weight) for weight in weights)
    bias_first = tuple(np.zeros_like(bias) for bias in biases)
    bias_second = tuple(np.zeros_like(bias) for bias in biases)
    row_count = int(fit_matrix.shape[0])
    step = 0
    trained_weights = weights
    trained_biases = biases
    for epoch_index in range(epoch_count):
        permutation_seed = batch_permutation_seed(root_seed, client_id, epoch_index)
        order = np.random.default_rng(thirty_two_bit_seed(permutation_seed)).permutation(row_count)
        shuffled = fit_matrix[order]
        for start in range(0, row_count, batch_size):
            batch = shuffled[start : start + batch_size]
            step += 1
            (
                trained_weights,
                trained_biases,
                first_moments,
                second_moments,
                bias_first,
                bias_second,
            ) = _adam_step(
                batch,
                trained_weights,
                trained_biases,
                first_moments,
                second_moments,
                bias_first,
                bias_second,
                learning_rate,
                beta_one,
                beta_two,
                optimizer_epsilon,
                weight_decay,
                step,
            )
    reconstructions = _forward(score_matrix, trained_weights, trained_biases)
    squared = np.square(score_matrix - reconstructions)
    per_sample = np.mean(squared, axis=1, dtype=np.float64)
    return tuple(float(value) for value in per_sample.tolist())


def _forward(
    inputs: NDArray[np.float32],
    weights: tuple[NDArray[np.float32], ...],
    biases: tuple[NDArray[np.float32], ...],
) -> NDArray[np.float32]:
    hidden = _relu(inputs @ weights[0] + biases[0])
    latent = _relu(hidden @ weights[1] + biases[1])
    decoded = _relu(latent @ weights[2] + biases[2])
    return decoded @ weights[3] + biases[3]


def _adam_step(
    batch: NDArray[np.float32],
    weights: tuple[NDArray[np.float32], ...],
    biases: tuple[NDArray[np.float32], ...],
    first_moments: tuple[NDArray[np.float32], ...],
    second_moments: tuple[NDArray[np.float32], ...],
    bias_first: tuple[NDArray[np.float32], ...],
    bias_second: tuple[NDArray[np.float32], ...],
    learning_rate: LearningRate,
    beta_one: FiniteFloat,
    beta_two: FiniteFloat,
    optimizer_epsilon: FiniteFloat,
    weight_decay: FiniteFloat,
    step: SolverIterationLimit,
) -> tuple[
    tuple[NDArray[np.float32], ...],
    tuple[NDArray[np.float32], ...],
    tuple[NDArray[np.float32], ...],
    tuple[NDArray[np.float32], ...],
    tuple[NDArray[np.float32], ...],
    tuple[NDArray[np.float32], ...],
]:
    hidden = _relu(batch @ weights[0] + biases[0])
    latent = _relu(hidden @ weights[1] + biases[1])
    decoded = _relu(latent @ weights[2] + biases[2])
    reconstruction = decoded @ weights[3] + biases[3]
    batch_size = float(batch.shape[0])
    feature_count = float(batch.shape[1])
    error = (reconstruction - batch) * np.float32(2.0 / (batch_size * feature_count))
    grad_w3 = decoded.T @ error
    grad_b3 = np.sum(error, axis=0)
    decoded_delta = (error @ weights[3].T) * (decoded > 0.0)
    grad_w2 = latent.T @ decoded_delta
    grad_b2 = np.sum(decoded_delta, axis=0)
    latent_delta = (decoded_delta @ weights[2].T) * (latent > 0.0)
    grad_w1 = hidden.T @ latent_delta
    grad_b1 = np.sum(latent_delta, axis=0)
    hidden_delta = (latent_delta @ weights[1].T) * (hidden > 0.0)
    grad_w0 = batch.T @ hidden_delta
    grad_b0 = np.sum(hidden_delta, axis=0)
    weight_grads = (grad_w0, grad_w1, grad_w2, grad_w3)
    bias_grads = (grad_b0, grad_b1, grad_b2, grad_b3)
    next_weights: list[NDArray[np.float32]] = []
    next_biases: list[NDArray[np.float32]] = []
    next_first: list[NDArray[np.float32]] = []
    next_second: list[NDArray[np.float32]] = []
    next_bias_first: list[NDArray[np.float32]] = []
    next_bias_second: list[NDArray[np.float32]] = []
    beta1 = np.float32(beta_one)
    beta2 = np.float32(beta_two)
    for index, weight in enumerate(weights):
        gradient = weight_grads[index] + np.float32(weight_decay) * weight
        first = beta1 * first_moments[index] + (1.0 - beta1) * gradient
        second = beta2 * second_moments[index] + (1.0 - beta2) * np.square(gradient)
        first_hat = first / (1.0 - (beta1**step))
        second_hat = second / (1.0 - (beta2**step))
        updated = weight - np.float32(learning_rate) * first_hat / (
            np.sqrt(second_hat) + np.float32(optimizer_epsilon)
        )
        next_weights.append(updated.astype(np.float32))
        next_first.append(first.astype(np.float32))
        next_second.append(second.astype(np.float32))
        bias_gradient = bias_grads[index]
        bias_m = beta1 * bias_first[index] + (1.0 - beta1) * bias_gradient
        bias_v = beta2 * bias_second[index] + (1.0 - beta2) * np.square(bias_gradient)
        bias_m_hat = bias_m / (1.0 - (beta1**step))
        bias_v_hat = bias_v / (1.0 - (beta2**step))
        updated_bias = biases[index] - np.float32(learning_rate) * bias_m_hat / (
            np.sqrt(bias_v_hat) + np.float32(optimizer_epsilon)
        )
        next_biases.append(updated_bias.astype(np.float32))
        next_bias_first.append(bias_m.astype(np.float32))
        next_bias_second.append(bias_v.astype(np.float32))
    return (
        tuple(next_weights),
        tuple(next_biases),
        tuple(next_first),
        tuple(next_second),
        tuple(next_bias_first),
        tuple(next_bias_second),
    )
