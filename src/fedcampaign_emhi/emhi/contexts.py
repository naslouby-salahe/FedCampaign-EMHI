import hashlib
from math import sqrt

import numpy as np
from numpy.typing import NDArray
from scipy.spatial.distance import cdist
from scipy.stats import norm

from fedcampaign_emhi.config.loading import histogram_edges
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
    PartitionRole,
)
from fedcampaign_emhi.domain.types import (
    BinCount,
    BinIndex,
    CellCount,
    ClientCount,
    ClientId,
    CoalitionMembers,
    ContextCentroids,
    ContextClusterIdentity,
    ContextTrainingRow,
    EpochCount,
    FiniteFloat,
    MaximalOutsideField,
    NumericalTolerance,
    OutsideContextHistogram,
    PositiveInt,
    Probability,
    RankValue,
    ResumeStep,
    SeedValue,
    SignedInt,
    SolverIterationLimit,
)
from fedcampaign_emhi.emhi.coalitions import complement_members, required_outside_client_count
from fedcampaign_emhi.runtime.determinism import canonical_utf8_bytes, thirty_two_bit_seed

STANDARD_NORMAL_QUARTILE: Probability = 1 / 4


def exact_exclusion_members(
    selected_client_ids: tuple[ClientId, ...],
    coalition_client_ids: tuple[ClientId, ...],
) -> tuple[ClientId, ...]:
    return complement_members(selected_client_ids, coalition_client_ids)


def inclusive_context_members(
    selected_client_ids: tuple[ClientId, ...],
    coalition_client_ids: tuple[ClientId, ...],
) -> tuple[ClientId, ...]:
    del coalition_client_ids
    return tuple(sorted(selected_client_ids))


def leave_one_out_context_members(
    selected_client_ids: tuple[ClientId, ...],
    coalition_client_ids: tuple[ClientId, ...],
) -> tuple[ClientId, ...]:
    if not coalition_client_ids:
        raise ValueError("leave-one-out exclusion requires a non-empty coalition")
    first_member = min(coalition_client_ids)
    return complement_members(selected_client_ids, (first_member,))


def partial_coalition_context_members(
    selected_client_ids: tuple[ClientId, ...],
    coalition_client_ids: tuple[ClientId, ...],
) -> tuple[ClientId, ...]:
    ordered = sorted(coalition_client_ids)
    if len(ordered) < 2:
        raise ValueError("partial coalition exclusion requires at least two members")
    removed_count = 2 if len(ordered) >= 3 else 1
    removed = tuple(ordered[:removed_count])
    return complement_members(selected_client_ids, removed)


ORACLE_QUARTILE_CELL_COUNT = 4
ORACLE_QUARTILE_BOUNDARIES: tuple[FiniteFloat, FiniteFloat, FiniteFloat] = (
    float(norm.ppf(STANDARD_NORMAL_QUARTILE)),
    0.0,
    float(norm.ppf(3 * STANDARD_NORMAL_QUARTILE)),
)
NO_OUTSIDE_CONTEXT_CELL_COUNT = 1


def oracle_outside_latent_cell(latent_state: FiniteFloat) -> BinIndex:
    boundaries = ORACLE_QUARTILE_BOUNDARIES
    for cell_index, boundary in enumerate(boundaries):
        if latent_state <= boundary:
            return cell_index
    return len(boundaries)


def shuffled_context_permutation(
    row_keys: tuple[ResumeStep, ...], split_role: PartitionRole, context_seed: SeedValue
) -> tuple[SignedInt, ...]:
    if not row_keys:
        raise ValueError("shuffled context requires lagged outside rows")
    payload_rows = [{"split": split_role.value, "row_key": key} for key in row_keys]
    digest = hashlib.sha256(
        canonical_utf8_bytes({"context_seed": context_seed, "rows": payload_rows})
    ).digest()
    generator = np.random.default_rng(int.from_bytes(digest[:8], "big"))
    permutation = generator.permutation(len(row_keys))
    return tuple(int(index) for index in permutation)


def local_history_context_member_ranks(
    coalition_client_ids: tuple[ClientId, ...],
    lagged_ranks: tuple[tuple[ClientId, RankValue], ...],
) -> tuple[RankValue, ...]:
    members = set(coalition_client_ids)
    return tuple(rank for client_id, rank in lagged_ranks if client_id in members)


def maximal_outside_field(
    selected_client_ids: tuple[ClientId, ...], coalition: CoalitionMembers
) -> MaximalOutsideField:
    complement = exact_exclusion_members(selected_client_ids, coalition.client_ids)
    return MaximalOutsideField(coalition=coalition, complement_client_ids=complement)


def nuisance_field_is_admissible(
    field_client_ids: tuple[ClientId, ...],
    selected_client_ids: tuple[ClientId, ...],
    coalition: CoalitionMembers,
) -> bool:
    outside = set(exact_exclusion_members(selected_client_ids, coalition.client_ids))
    return all(client_id in outside for client_id in field_client_ids)


def histogram_bin_index(rank: RankValue, bin_count: BinCount) -> BinIndex:
    raw_index = int(rank * bin_count)
    last_index = bin_count - 1
    if raw_index > last_index:
        return last_index
    return raw_index


def equal_width_histogram_edges(bin_count: BinCount) -> tuple[RankValue, ...]:
    return histogram_edges(bin_count)


def histogram_one_hot(rank: RankValue, bin_count: BinCount) -> tuple[FiniteFloat, ...]:
    assigned = histogram_bin_index(rank, bin_count)
    return tuple(1.0 if index == assigned else 0.0 for index in range(bin_count))


def outside_availability_is_sufficient(
    available_client_ids: tuple[ClientId, ...],
    complement_client_ids: tuple[ClientId, ...],
    minimum_available_outside_clients: ClientCount,
    minimum_available_outside_fraction: Probability,
) -> bool:
    complement = set(complement_client_ids)
    if any(client_id not in complement for client_id in available_client_ids):
        return False
    required = required_outside_client_count(
        len(complement_client_ids),
        minimum_available_outside_clients,
        minimum_available_outside_fraction,
    )
    return len(available_client_ids) >= required


def outside_context_histogram(
    lagged_ranks: tuple[tuple[ClientId, RankValue], ...],
    available_client_ids: tuple[ClientId, ...],
    complement_client_ids: tuple[ClientId, ...],
    bin_count: BinCount,
    minimum_available_outside_clients: ClientCount,
    minimum_available_outside_fraction: Probability,
) -> OutsideContextHistogram:
    if not outside_availability_is_sufficient(
        available_client_ids,
        complement_client_ids,
        minimum_available_outside_clients,
        minimum_available_outside_fraction,
    ):
        zeros = tuple(0.0 for _index in range(bin_count))
        return OutsideContextHistogram(
            bin_mass=zeros, available_client_ids=available_client_ids, abstained=True
        )
    available = set(available_client_ids)
    selected_ranks = tuple(rank for client_id, rank in lagged_ranks if client_id in available)
    mass = [0.0 for _index in range(bin_count)]
    for rank in selected_ranks:
        one_hot = histogram_one_hot(rank, bin_count)
        for index, contribution in enumerate(one_hot):
            mass[index] += contribution
    scale = 1.0 / len(available_client_ids)
    return OutsideContextHistogram(
        bin_mass=tuple(scale * total for total in mass),
        available_client_ids=available_client_ids,
        abstained=False,
    )


def context_cluster_identity(
    dataset: DatasetName,
    coalition_order: CoalitionOrder,
    context_method: ContextMethodName,
    experiment_seed: SeedValue | None,
) -> ContextClusterIdentity:
    return ContextClusterIdentity(
        dataset=dataset,
        coalition_order=coalition_order,
        context_method=context_method,
        experiment_seed=experiment_seed,
    )


def context_row_ranking_value(row: ContextTrainingRow, context_seed: SeedValue) -> SeedValue:
    payload: YamlNode = {
        "context_seed": context_seed,
        "dataset": row.dataset.value,
        "coalition_order": int(row.coalition_order),
        "coalition_client_ids": list(row.coalition_client_ids),
        "epoch_index": row.epoch_index,
    }
    digest = hashlib.sha256(canonical_utf8_bytes(payload)).digest()
    return int.from_bytes(digest[:8], "big")


def cap_context_training_rows(
    rows: tuple[ContextTrainingRow, ...],
    context_seed: SeedValue,
    max_fit_rows: PositiveInt,
) -> tuple[ContextTrainingRow, ...]:
    ranked = sorted(
        rows,
        key=lambda row: (
            context_row_ranking_value(row, context_seed),
            row.coalition_client_ids,
            row.epoch_index,
        ),
    )
    return tuple(ranked[:max_fit_rows])


def assign_context_cell(
    histogram: tuple[FiniteFloat, ...],
    centroids: tuple[tuple[FiniteFloat, ...], ...],
    assignment_tie_tolerance: NumericalTolerance,
) -> BinIndex:
    distances = tuple(_euclidean_distance(histogram, centroid) for centroid in centroids)
    best = min(distances)
    tied = tuple(
        index
        for index, distance in enumerate(distances)
        if distance - best <= assignment_tie_tolerance
    )
    return tied[0]


def fit_context_centroids(
    rows: tuple[ContextTrainingRow, ...],
    identity: ContextClusterIdentity,
    cell_count: CellCount,
    n_init: PositiveInt,
    max_iterations: SolverIterationLimit,
    tolerance: NumericalTolerance,
    assignment_tie_tolerance: NumericalTolerance,
    seed: SeedValue,
) -> ContextCentroids | None:
    if len(rows) < cell_count:
        return None
    matrix = np.asarray([row.histogram for row in rows], dtype=np.float64)
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    best_centroids: NDArray[np.float64] | None = None
    best_inertia = None
    for _restart in range(n_init):
        centroids, inertia = _lloyd_kmeans(
            matrix, cell_count, max_iterations, tolerance, assignment_tie_tolerance, generator
        )
        if best_inertia is None or inertia < best_inertia:
            best_inertia = inertia
            best_centroids = centroids
    if best_centroids is None:
        return None
    packed = tuple(
        tuple(float(coordinate) for coordinate in centroid) for centroid in best_centroids
    )
    return ContextCentroids(identity=identity, centroids=packed)


def minimum_support_epochs_for_order(
    order: CoalitionOrder, order_one: EpochCount, order_two: EpochCount, order_three: EpochCount
) -> EpochCount:
    if order is CoalitionOrder.ONE:
        return order_one
    if order is CoalitionOrder.TWO:
        return order_two
    return order_three


def coalition_context_support_is_sufficient(
    observation_count: EpochCount, required_epochs: EpochCount
) -> bool:
    return observation_count >= required_epochs


def _euclidean_distance(
    left: tuple[FiniteFloat, ...], right: tuple[FiniteFloat, ...]
) -> FiniteFloat:
    return sqrt(sum((left[index] - right[index]) ** 2 for index in range(len(left))))


def _lloyd_kmeans(
    matrix: NDArray[np.float64],
    cell_count: CellCount,
    max_iterations: SolverIterationLimit,
    tolerance: NumericalTolerance,
    assignment_tie_tolerance: NumericalTolerance,
    generator: np.random.Generator,
) -> tuple[NDArray[np.float64], FiniteFloat]:
    row_count = int(matrix.shape[0])
    chosen = generator.choice(row_count, size=cell_count, replace=False)
    centroids = matrix[chosen].copy()
    assignments = np.zeros(row_count, dtype=np.int64)
    for _iteration in range(max_iterations):
        distances = cdist(matrix, centroids)
        best = distances.min(axis=1, keepdims=True)
        within_tolerance = (distances - best) <= assignment_tie_tolerance
        assignments = within_tolerance.argmax(axis=1)
        updated = centroids.copy()
        for cell_index in range(cell_count):
            members = matrix[assignments == cell_index]
            if members.shape[0] == 0:
                updated[cell_index] = matrix[int(generator.integers(0, row_count))]
            else:
                updated[cell_index] = np.mean(members, axis=0)
        shift = float(np.max(np.linalg.norm(updated - centroids, axis=1)))
        centroids = updated
        if shift <= tolerance:
            break
    inertia = 0.0
    for row_index in range(row_count):
        centroid = np.asarray(centroids[int(assignments[row_index])], dtype=np.float64)
        residual = np.asarray(matrix[row_index] - centroid, dtype=np.float64)
        inertia += float(np.sum(np.square(residual)))
    return centroids, inertia
