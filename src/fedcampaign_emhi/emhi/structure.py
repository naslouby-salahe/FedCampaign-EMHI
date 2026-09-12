from bisect import bisect_left, bisect_right
from collections.abc import Mapping
from itertools import combinations
from math import ceil, comb, sqrt

from scipy.stats import norm

from fedcampaign_emhi.artifacts.records import (
    ClientMarginalRankStream,
    DetectorScoreArtifactRecord,
    MarginalRankArtifactRecord,
)
from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import (
    BasisCoordinate,
    BasisSize,
    ClientCount,
    ClientId,
    CoalitionCount,
    CoalitionMembers,
    DetectorScore,
    EpochIndexValue,
    GaussianCoordinate,
    MaterialDependencyFingerprint,
    NumericalFloor,
    Probability,
    RankReference,
    RankValue,
    TensorDimension,
)


def coalition_count(client_count: ClientCount, maximum_order: CoalitionOrder) -> CoalitionCount:
    return sum(comb(client_count, order) for order in range(1, maximum_order + 1))


def required_outside_client_count(
    complement_size: ClientCount,
    minimum_available_outside_clients: ClientCount,
    minimum_available_outside_fraction: Probability,
) -> ClientCount:
    fractional = ceil(minimum_available_outside_fraction * complement_size)
    return max(minimum_available_outside_clients, fractional)


def enumerate_coalitions(
    client_ids: tuple[ClientId, ...], maximum_order: CoalitionOrder
) -> tuple[CoalitionMembers, ...]:
    ordered = tuple(sorted(client_ids))
    coalitions: list[CoalitionMembers] = []
    for order in range(1, maximum_order + 1):
        coalition_order = CoalitionOrder(order)
        for members in combinations(ordered, order):
            coalitions.append(CoalitionMembers(client_ids=members, order=coalition_order))
    return tuple(coalitions)


def complement_members(
    selected_client_ids: tuple[ClientId, ...], coalition_client_ids: tuple[ClientId, ...]
) -> tuple[ClientId, ...]:
    coalition = set(coalition_client_ids)
    return tuple(client_id for client_id in selected_client_ids if client_id not in coalition)


def proper_subset_members(coalition: CoalitionMembers) -> tuple[CoalitionMembers, ...]:
    subsets: list[CoalitionMembers] = []
    for order in range(1, coalition.order):
        coalition_order = CoalitionOrder(order)
        for members in combinations(coalition.client_ids, order):
            subsets.append(CoalitionMembers(client_ids=members, order=coalition_order))
    return tuple(subsets)


def clip_rank(rank: RankValue, epsilon: NumericalFloor) -> RankValue:
    if rank < epsilon:
        return epsilon
    upper = 1.0 - epsilon  # TODO: should be constant
    if rank > upper:
        return upper
    return rank


def midrank(score: DetectorScore, reference: RankReference) -> RankValue:
    observation_count = len(reference.scores)
    if observation_count == 0:
        raise ValueError("rank reference must contain at least one score")
    less = sum(1 for reference_score in reference.scores if reference_score < score)
    equal = sum(1 for reference_score in reference.scores if reference_score == score)
    return (less + (0.5 * equal) + 0.5) / (observation_count + 1)  # TODO: should be constant


def clipped_midrank(
    score: DetectorScore, reference: RankReference, epsilon: NumericalFloor
) -> RankValue:
    return clip_rank(midrank(score, reference), epsilon)


def sorted_clipped_midrank(
    score: DetectorScore,
    sorted_reference_scores: tuple[RankValue, ...],
    epsilon: NumericalFloor,
) -> RankValue:
    observation_count = len(sorted_reference_scores)
    if observation_count == 0:
        raise ValueError("rank reference must contain at least one score")
    less = bisect_left(sorted_reference_scores, score)
    equal = bisect_right(sorted_reference_scores, score) - less
    rank = (less + (0.5 * equal) + 0.5) / (observation_count + 1)
    return clip_rank(rank, epsilon)


def coalition_conditioned_residual_rank(
    marginal_rank: RankValue, context_reference: RankReference, epsilon: NumericalFloor
) -> RankValue:
    return clipped_midrank(marginal_rank, context_reference, epsilon)


def batch_clipped_midrank(
    scores: tuple[DetectorScore, ...], reference: RankReference, epsilon: NumericalFloor
) -> tuple[RankValue, ...]:
    observation_count = len(reference.scores)
    if observation_count == 0:
        raise ValueError("rank reference must contain at least one score")
    sorted_reference = sorted(reference.scores)
    ranks: list[RankValue] = []
    for score in scores:
        less = bisect_left(sorted_reference, score)
        equal = bisect_right(sorted_reference, score) - less
        rank = (less + (0.5 * equal) + 0.5) / (observation_count + 1)
        ranks.append(clip_rank(rank, epsilon))
    return tuple(ranks)


_cached_rank_stream_fingerprint: MaterialDependencyFingerprint | None = None
_cached_rank_streams: Mapping[ClientId, ClientMarginalRankStream] | None = None


def _client_rank_streams(
    ranks: MarginalRankArtifactRecord,
) -> Mapping[ClientId, ClientMarginalRankStream]:
    global _cached_rank_stream_fingerprint, _cached_rank_streams
    if (
        _cached_rank_stream_fingerprint == ranks.dependency_fingerprint
        and _cached_rank_streams is not None
    ):
        return _cached_rank_streams
    built = {stream.client_id: stream for stream in ranks.client_streams}
    _cached_rank_stream_fingerprint = ranks.dependency_fingerprint
    _cached_rank_streams = built
    return built


def clear_rank_lookup_cache() -> None:
    global _cached_rank_stream_fingerprint, _cached_rank_streams
    _cached_rank_stream_fingerprint = None
    _cached_rank_streams = None


def rank_at_epoch(
    ranks: MarginalRankArtifactRecord,
    client_id: ClientId,
    epoch_index: EpochIndexValue,
) -> RankValue | None:
    stream = _client_rank_streams(ranks).get(client_id)
    if stream is None:
        return None
    if not stream.epoch_indexes:
        return None
    position = epoch_index - stream.epoch_indexes[0]
    if 0 <= position < len(stream.epoch_indexes) and stream.epoch_indexes[position] == epoch_index:
        return stream.ranks[position]
    position = bisect_left(stream.epoch_indexes, epoch_index)
    if position == len(stream.epoch_indexes) or stream.epoch_indexes[position] != epoch_index:
        return None
    return stream.ranks[position]


def build_marginal_rank_artifact(
    scores: DetectorScoreArtifactRecord,
    reference_epochs: tuple[EpochIndexValue, ...],
    rank_clip_epsilon: NumericalFloor,
    dependency_fingerprint: MaterialDependencyFingerprint,
) -> MarginalRankArtifactRecord:
    reference_epoch_set = set(reference_epochs)
    streams: list[ClientMarginalRankStream] = []
    for score_stream in scores.client_streams:
        reference_scores = tuple(
            score
            for epoch, score in zip(
                score_stream.epoch_indexes,
                score_stream.scores,
                strict=True,
            )
            if epoch in reference_epoch_set
        )
        if not reference_scores:
            raise ValueError(
                f"client {score_stream.client_id} has no nuisance-fit rank reference scores"
            )
        reference = RankReference(scores=reference_scores)
        ranks = batch_clipped_midrank(score_stream.scores, reference, rank_clip_epsilon)
        streams.append(
            ClientMarginalRankStream(
                client_id=score_stream.client_id,
                nuisance_reference_scores=reference_scores,
                epoch_indexes=score_stream.epoch_indexes,
                ranks=ranks,
            )
        )
    return MarginalRankArtifactRecord(
        dataset_name=scores.dataset_name,
        root_seed=scores.root_seed,
        selected_client_ids=scores.selected_client_ids,
        client_streams=tuple(streams),
        dependency_fingerprint=dependency_fingerprint,
    )


def shifted_legendre_phi_one(rank: RankValue) -> BasisCoordinate:
    return sqrt(3.0) * ((2.0 * rank) - 1.0)


def shifted_legendre_phi_two(rank: RankValue) -> BasisCoordinate:
    return sqrt(5.0) * ((6.0 * (rank**2)) - (6.0 * rank) + 1.0)


def shifted_legendre_phi_three(rank: RankValue) -> BasisCoordinate:
    return sqrt(7.0) * ((20.0 * (rank**3)) - (30.0 * (rank**2)) + (12.0 * rank) - 1.0)


def shifted_legendre_phi_four(rank: RankValue) -> BasisCoordinate:
    return 3.0 * (
        (70.0 * (rank**4)) - (140.0 * (rank**3)) + (90.0 * (rank**2)) - (20.0 * rank) + 1.0
    )


def bounded_basis(rank: RankValue, basis_size: BasisSize) -> tuple[BasisCoordinate, ...]:
    if basis_size == 1:  # TODO: should be constant
        return (shifted_legendre_phi_one(rank),)
    if basis_size == 2:  # TODO: should be constant
        return (shifted_legendre_phi_one(rank), shifted_legendre_phi_two(rank))
    if basis_size == 3:  # TODO: should be constant
        return (
            shifted_legendre_phi_one(rank),
            shifted_legendre_phi_two(rank),
            shifted_legendre_phi_three(rank),
        )
    if basis_size == 4:  # TODO: should be constant
        return (
            shifted_legendre_phi_one(rank),
            shifted_legendre_phi_two(rank),
            shifted_legendre_phi_three(rank),
            shifted_legendre_phi_four(rank),
        )
    raise ValueError("basis_size must be between 1 and 4 inclusive")


def tensor_dimension(basis_size: BasisSize, coalition_order: CoalitionOrder) -> TensorDimension:
    return basis_size**coalition_order


def tensor_representation(
    member_ranks: tuple[RankValue, ...], basis_size: BasisSize
) -> tuple[BasisCoordinate, ...]:
    if not member_ranks:
        raise ValueError("tensor representation requires at least one coalition member")
    coordinates = [1.0]
    for rank in member_ranks:
        member_basis = bounded_basis(rank, basis_size)
        expanded = []
        for left in coordinates:
            for right in member_basis:
                expanded.append(left * right)
        coordinates = expanded
    return tuple(coordinates)


def standard_normal_cdf(gaussian_coordinate: GaussianCoordinate) -> RankValue:
    return float(norm.cdf(gaussian_coordinate))
