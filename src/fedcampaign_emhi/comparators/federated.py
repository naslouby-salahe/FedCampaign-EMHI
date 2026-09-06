import socket
import threading
import time
from typing import cast

import flwr as fl
import numpy as np
import torch
from flwr.common import (
    Config,
    FitIns,
    FitRes,
    Metrics,
    NDArrays,
    Parameters,
    ndarrays_to_parameters,
    parameters_to_ndarrays,
)
from flwr.server import ServerConfig, start_server
from flwr.server.client_manager import ClientManager
from flwr.server.client_proxy import ClientProxy
from flwr.server.strategy import Strategy
from numpy.typing import NDArray

from fedcampaign_emhi.domain.types import (
    AutoencoderBeta,
    BatchSize,
    ClientCount,
    ClientId,
    FeatureDimension,
    FeatureValue,
    FederatedRoundCount,
    LearningRate,
    LoopbackPortNumber,
    MetricValue,
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
    AutoencoderNetwork,
    FittedAutoencoder,
    build_autoencoder_network,
    train_autoencoder_epochs,
)
from fedcampaign_emhi.runtime import derive_component_seed, thirty_two_bit_seed

PARTICIPATION_COMPONENT_NAME = "fedavg_autoencoder_participation"
SERVER_ROUND_CONFIG_KEY = "server_round"
CLIENT_INDEX_CONFIG_KEY = "client_index"
CONNECT_DEADLINE_SECONDS = 30
CONNECT_RETRY_SLEEP_SECONDS = 0.5


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
            component_name=PARTICIPATION_COMPONENT_NAME,
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


def _network_parameters(network: AutoencoderNetwork) -> tuple[NDArray[np.float32], ...]:
    return tuple(param.detach().numpy().copy() for param in network.parameters())


def _load_network_parameters(
    network: AutoencoderNetwork, parameters: tuple[NDArray[np.float32], ...]
) -> None:
    with torch.no_grad():
        for parameter, values in zip(network.parameters(), parameters, strict=True):
            parameter.copy_(torch.from_numpy(values))


def _rows_tensor(rows: tuple[tuple[FeatureValue, ...], ...]) -> torch.Tensor:
    return torch.tensor(rows, dtype=torch.float32)


def _aligned_client_rows(
    client_fit_rows: tuple[tuple[tuple[FeatureValue, ...], ...], ...],
    client_ids: tuple[ClientId, ...],
) -> tuple[tuple[torch.Tensor, ...], tuple[RecordCount, ...]]:
    if not client_fit_rows or len(client_fit_rows) != len(client_ids):
        raise ValueError("FedAvg autoencoder requires aligned per-client detector-fit rows")
    matrices: list[torch.Tensor] = []
    counts: list[RecordCount] = []
    for rows in client_fit_rows:
        matrix = _rows_tensor(rows)
        if int(matrix.shape[0]) == 0:
            raise ValueError("FedAvg autoencoder requires non-empty per-client detector-fit rows")
        matrices.append(matrix)
        counts.append(int(matrix.shape[0]))
    return tuple(matrices), tuple(counts)


class FedAvgServerStrategy:
    def __init__(
        self,
        *,
        initial_parameters: Parameters,
        min_fit_clients: ClientCount,
    ) -> None:
        self.initial_parameters = initial_parameters
        self.min_fit_clients = min_fit_clients
        self.latest_parameters: tuple[NDArray[np.float32], ...] = ()

    def initialize_parameters(self, client_manager: ClientManager) -> Parameters | None:
        return self.initial_parameters

    def evaluate(
        self, server_round: FederatedRoundCount, parameters: Parameters
    ) -> tuple[MetricValue, Metrics] | None:
        return None

    def configure_evaluate(
        self,
        server_round: FederatedRoundCount,
        parameters: Parameters,
        client_manager: ClientManager,
    ) -> tuple[tuple[ClientProxy, FitIns], ...]:
        return ()

    def aggregate_evaluate(
        self,
        server_round: FederatedRoundCount,
        results: tuple[tuple[ClientProxy, FitRes], ...],
        failures: tuple[tuple[ClientProxy, FitRes] | BaseException, ...],
    ) -> tuple[MetricValue, Metrics] | None:
        return None

    def configure_fit(
        self,
        server_round: FederatedRoundCount,
        parameters: Parameters,
        client_manager: ClientManager,
    ) -> tuple[tuple[ClientProxy, FitIns], ...]:
        deadline = time.monotonic() + CONNECT_DEADLINE_SECONDS
        while True:
            proxies = sorted(client_manager.all().values(), key=lambda proxy: proxy.cid)
            if len(proxies) >= self.min_fit_clients:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("FedAvg server could not reach its required clients")
            time.sleep(CONNECT_RETRY_SLEEP_SECONDS)
        config: Config = {SERVER_ROUND_CONFIG_KEY: server_round}
        fit_ins = FitIns(parameters=parameters, config=config)
        return tuple((proxy, fit_ins) for proxy in proxies)

    def aggregate_fit(
        self,
        server_round: FederatedRoundCount,
        results: tuple[tuple[ClientProxy, FitRes], ...],
        failures: tuple[tuple[ClientProxy, FitRes] | BaseException, ...],
    ) -> tuple[Parameters | None, Metrics]:
        if not results:
            return None, {}
        indexed_results: list[tuple[RecordCount, RecordCount, tuple[NDArray[np.float32], ...]]] = []
        for _proxy, fit_result in results:
            client_index = int(cast(str, fit_result.metrics[CLIENT_INDEX_CONFIG_KEY]))
            num_examples = int(fit_result.num_examples)
            layers = tuple(
                cast(NDArray[np.float32], layer)
                for layer in parameters_to_ndarrays(fit_result.parameters)
            )
            indexed_results.append((client_index, num_examples, layers))
        indexed_results.sort(key=lambda item: item[0])
        total_samples = sum(num_examples for _index, num_examples, _values in indexed_results)
        if total_samples <= 0:
            raise ValueError("FedAvg aggregation requires positive total sample count")
        layer_count = len(indexed_results[0][2])
        aggregated: list[NDArray[np.float32]] = []
        for layer_index in range(layer_count):
            accumulation: NDArray[np.float64] = np.zeros_like(
                indexed_results[0][2][layer_index], dtype=np.float64
            )
            for _index, num_examples, values in indexed_results:
                weighted_layer = np.asarray(values[layer_index], dtype=np.float64) * num_examples
                accumulation += weighted_layer
            aggregated.append((accumulation / total_samples).astype(np.float32))
        self.latest_parameters = tuple(aggregated)
        return ndarrays_to_parameters(aggregated), {}


class FedAvgClient(fl.client.NumPyClient):
    def __init__(
        self,
        client_index: RecordCount,
        fit_matrix: torch.Tensor,
        row_count: RecordCount,
        input_dimension: FeatureDimension,
        client_ids: tuple[ClientId, ...],
        local_epochs_per_round: SolverIterationLimit,
        participation_fraction: Probability,
        learning_rate: LearningRate,
        beta_one: AutoencoderBeta,
        beta_two: AutoencoderBeta,
        optimizer_epsilon: NumericalFloor,
        weight_decay: WeightDecay,
        batch_size: BatchSize,
        root_seed: SeedValue,
    ) -> None:
        self.client_index = client_index
        self.fit_matrix = fit_matrix
        self.row_count = row_count
        self.input_dimension = input_dimension
        self.client_ids = client_ids
        self.local_epochs_per_round = local_epochs_per_round
        self.participation_fraction = participation_fraction
        self.learning_rate = learning_rate
        self.beta_one = beta_one
        self.beta_two = beta_two
        self.optimizer_epsilon = optimizer_epsilon
        self.weight_decay = weight_decay
        self.batch_size = batch_size
        self.root_seed = root_seed
        self.parameters: tuple[NDArray[np.float32], ...] = ()

    def _network(self) -> AutoencoderNetwork:
        network = build_autoencoder_network(self.input_dimension, self.root_seed)
        if self.parameters:
            _load_network_parameters(network, self.parameters)
        return network

    def get_parameters(self, config: Config) -> NDArrays:
        return list(self.parameters)

    def fit(
        self,
        parameters: NDArrays,
        config: Config,
    ) -> tuple[NDArrays, RecordCount, Metrics]:
        self.parameters = tuple(np.asarray(values, dtype=np.float32) for values in parameters)
        server_round = cast(int, config[SERVER_ROUND_CONFIG_KEY])
        participation_count = max(1, round(self.participation_fraction * len(self.client_ids)))
        participating = fedavg_participant_indexes(
            len(self.client_ids),
            participation_count,
            self.root_seed,
            self.client_ids,
            server_round - 1,
        )
        if self.client_index not in participating:
            return list(self.parameters), 0, {CLIENT_INDEX_CONFIG_KEY: str(self.client_index)}
        network = self._network()
        epoch_offset = (server_round - 1) * self.local_epochs_per_round
        train_autoencoder_epochs(
            network,
            self.fit_matrix,
            self.learning_rate,
            self.beta_one,
            self.beta_two,
            self.optimizer_epsilon,
            self.weight_decay,
            self.batch_size,
            self.local_epochs_per_round,
            self.root_seed,
            self.client_ids[self.client_index],
            epoch_offset,
        )
        self.parameters = _network_parameters(network)
        return (
            list(self.parameters),
            self.row_count,
            {CLIENT_INDEX_CONFIG_KEY: str(self.client_index)},
        )

    def evaluate(
        self,
        parameters: NDArrays,
        config: Config,
    ) -> tuple[MetricValue, RecordCount, Metrics]:
        return 0.0, self.row_count, {}


def _free_loopback_port() -> LoopbackPortNumber:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def fit_federated_autoencoder(
    client_fit_rows: tuple[tuple[tuple[FeatureValue, ...], ...], ...],
    client_ids: tuple[ClientId, ...],
    rounds: FederatedRoundCount,
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
    matrices, row_counts = _aligned_client_rows(client_fit_rows, client_ids)
    input_dimension = int(matrices[0].shape[1])
    global_network = build_autoencoder_network(input_dimension, root_seed)
    initial_parameters = _network_parameters(global_network)
    strategy = FedAvgServerStrategy(
        initial_parameters=ndarrays_to_parameters(list(initial_parameters)),
        min_fit_clients=len(client_ids),
    )
    port = _free_loopback_port()
    threads: list[threading.Thread] = []
    for client_index in range(len(client_ids)):
        client = FedAvgClient(
            client_index,
            matrices[client_index],
            row_counts[client_index],
            input_dimension,
            client_ids,
            local_epochs_per_round,
            client_participation_fraction,
            learning_rate,
            beta_one,
            beta_two,
            optimizer_epsilon,
            weight_decay,
            batch_size,
            root_seed,
        )
        thread = threading.Thread(target=_run_client, args=(port, client), daemon=True)
        threads.append(thread)
        thread.start()
    start_server(
        server_address=f"127.0.0.1:{port}",
        config=ServerConfig(num_rounds=rounds),
        strategy=cast(Strategy, strategy),
    )
    for thread in threads:
        thread.join()
    fitted_network = build_autoencoder_network(input_dimension, root_seed)
    _load_network_parameters(fitted_network, strategy.latest_parameters)
    return FittedAutoencoder(fitted_network)


def _run_client(port: LoopbackPortNumber, client: FedAvgClient) -> None:
    deadline = time.monotonic() + CONNECT_DEADLINE_SECONDS
    while True:
        try:
            fl.client.start_client(
                server_address=f"127.0.0.1:{port}",
                client=client.to_client(),
            )
            return
        except Exception as error:
            if time.monotonic() >= deadline:
                raise RuntimeError("FedAvg client could not complete training") from error
            time.sleep(CONNECT_RETRY_SLEEP_SECONDS)
