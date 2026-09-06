import math

import torch
from torch import nn

from fedcampaign_emhi.domain.types import (
    AnomalyScore,
    AutoencoderBeta,
    BatchSize,
    ClientId,
    FeatureDimension,
    FeatureValue,
    LayerWidth,
    LearningRate,
    NumericalFloor,
    SeedCoordinate,
    SeedDerivationIdentity,
    SeedValue,
    SolverIterationLimit,
    WeightDecay,
    XavierGain,
)
from fedcampaign_emhi.runtime import derive_component_seed, log_stage, thirty_two_bit_seed

AUTOENCODER_ENCODER_WIDTH: LayerWidth = 32
AUTOENCODER_LATENT_WIDTH: LayerWidth = 8
AUTOENCODER_DECODER_WIDTH: LayerWidth = 32
RELU_XAVIER_GAIN: XavierGain = math.sqrt(2.0)
OUTPUT_XAVIER_GAIN: XavierGain = 1.0

torch.set_num_threads(1)


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


class AutoencoderNetwork(nn.Module):
    encoder: nn.Linear
    latent: nn.Linear
    decoder: nn.Linear
    output_layer: nn.Linear

    def __init__(self, input_dimension: FeatureDimension) -> None:
        super().__init__()
        self.encoder = nn.Linear(input_dimension, AUTOENCODER_ENCODER_WIDTH)
        self.latent = nn.Linear(AUTOENCODER_ENCODER_WIDTH, AUTOENCODER_LATENT_WIDTH)
        self.decoder = nn.Linear(AUTOENCODER_LATENT_WIDTH, AUTOENCODER_DECODER_WIDTH)
        self.output_layer = nn.Linear(AUTOENCODER_DECODER_WIDTH, input_dimension)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        hidden = torch.relu(self.encoder(inputs))
        latent = torch.relu(self.latent(hidden))
        decoded = torch.relu(self.decoder(latent))
        return self.output_layer(decoded)


def build_autoencoder_network(
    input_dimension: FeatureDimension, root_seed: SeedValue
) -> AutoencoderNetwork:
    generator = torch.Generator()
    generator.manual_seed(thirty_two_bit_seed(root_seed))
    network = AutoencoderNetwork(input_dimension)
    for layer, gain in (
        (network.encoder, RELU_XAVIER_GAIN),
        (network.latent, RELU_XAVIER_GAIN),
        (network.decoder, RELU_XAVIER_GAIN),
    ):
        nn.init.xavier_uniform_(layer.weight, gain=gain, generator=generator)
        nn.init.zeros_(layer.bias)
    nn.init.xavier_uniform_(
        network.output_layer.weight, gain=OUTPUT_XAVIER_GAIN, generator=generator
    )
    nn.init.zeros_(network.output_layer.bias)
    return network


class FittedAutoencoder:
    __slots__ = ("_network",)

    def __init__(self, network: AutoencoderNetwork) -> None:
        self._network = network

    def score(self, score_rows: tuple[tuple[FeatureValue, ...], ...]) -> tuple[AnomalyScore, ...]:
        score_matrix = torch.tensor(score_rows, dtype=torch.float32)
        with torch.no_grad():
            reconstruction = self._network(score_matrix)
            squared = torch.square(score_matrix - reconstruction)
            per_sample = squared.to(torch.float64).mean(dim=1)
        sample_count = int(per_sample.shape[0])
        return tuple(float(per_sample[index].item()) for index in range(sample_count))


def train_autoencoder_epochs(
    network: AutoencoderNetwork,
    fit_matrix: torch.Tensor,
    learning_rate: LearningRate,
    beta_one: AutoencoderBeta,
    beta_two: AutoencoderBeta,
    optimizer_epsilon: NumericalFloor,
    weight_decay: WeightDecay,
    batch_size: BatchSize,
    epoch_count: SolverIterationLimit,
    root_seed: SeedValue,
    client_id: ClientId,
    epoch_offset: SolverIterationLimit,
) -> None:
    optimizer = torch.optim.Adam(
        [
            {
                "params": (
                    network.encoder.weight,
                    network.latent.weight,
                    network.decoder.weight,
                    network.output_layer.weight,
                ),
                "weight_decay": weight_decay,
            },
            {
                "params": (
                    network.encoder.bias,
                    network.latent.bias,
                    network.decoder.bias,
                    network.output_layer.bias,
                ),
                "weight_decay": 0.0,
            },
        ],
        lr=learning_rate,
        betas=(beta_one, beta_two),
        eps=optimizer_epsilon,
    )
    criterion = nn.MSELoss()
    row_count = int(fit_matrix.shape[0])
    for local_epoch_index in range(epoch_count):
        permutation_seed = batch_permutation_seed(
            root_seed, client_id, epoch_offset + local_epoch_index
        )
        generator = torch.Generator()
        generator.manual_seed(thirty_two_bit_seed(permutation_seed))
        order = torch.randperm(row_count, generator=generator)
        shuffled = fit_matrix[order]
        for start in range(0, row_count, batch_size):
            batch = shuffled[start : start + batch_size]
            optimizer.zero_grad(set_to_none=True)
            reconstruction = network(batch)
            loss = criterion(reconstruction, batch)
            loss.backward()
            optimizer.step()


def _fit_matrix(fit_rows: tuple[tuple[FeatureValue, ...], ...]) -> torch.Tensor:
    if not fit_rows:
        raise ValueError("autoencoder requires a non-empty detector-fit matrix")
    return torch.tensor(fit_rows, dtype=torch.float32)


@log_stage("models.autoencoder")
def fit_autoencoder(
    fit_rows: tuple[tuple[FeatureValue, ...], ...],
    learning_rate: LearningRate,
    beta_one: AutoencoderBeta,
    beta_two: AutoencoderBeta,
    optimizer_epsilon: NumericalFloor,
    weight_decay: WeightDecay,
    batch_size: BatchSize,
    epoch_count: SolverIterationLimit,
    root_seed: SeedValue,
    client_id: ClientId,
) -> FittedAutoencoder:
    fit_matrix = _fit_matrix(fit_rows)
    input_dimension = int(fit_matrix.shape[1])
    network = build_autoencoder_network(input_dimension, root_seed)
    train_autoencoder_epochs(
        network,
        fit_matrix,
        learning_rate,
        beta_one,
        beta_two,
        optimizer_epsilon,
        weight_decay,
        batch_size,
        epoch_count,
        root_seed,
        client_id,
        0,
    )
    return FittedAutoencoder(network)


def autoencoder_anomaly_scores(
    fit_rows: tuple[tuple[FeatureValue, ...], ...],
    score_rows: tuple[tuple[FeatureValue, ...], ...],
    learning_rate: LearningRate,
    beta_one: AutoencoderBeta,
    beta_two: AutoencoderBeta,
    optimizer_epsilon: NumericalFloor,
    weight_decay: WeightDecay,
    batch_size: BatchSize,
    epoch_count: SolverIterationLimit,
    root_seed: SeedValue,
    client_id: ClientId,
) -> tuple[AnomalyScore, ...]:
    fitted = fit_autoencoder(
        fit_rows,
        learning_rate,
        beta_one,
        beta_two,
        optimizer_epsilon,
        weight_decay,
        batch_size,
        epoch_count,
        root_seed,
        client_id,
    )
    return fitted.score(score_rows)
