from dataclasses import dataclass
from math import floor, sqrt

import numpy as np

from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExperimentState
from fedcampaign_emhi.domain.types import (
    Boolean,
    ClientCount,
    ClientId,
    ClientLoading,
    ComponentName,
    Correlation,
    DetectorScore,
    FractionalClientCount,
    LatentAutoregressiveCoefficient,
    LatentState,
    NumericalFloor,
    PositiveEpochCount,
    Probability,
    RankValue,
    ScoreShift,
    SeedValue,
    StandardDeviation,
)
from fedcampaign_emhi.emhi.structure import required_outside_client_count, standard_normal_cdf
from fedcampaign_emhi.runtime import thirty_two_bit_seed
from fedcampaign_emhi.synthetic.pure_order import lexicographic_target_clients


def equally_spaced_loadings(
    client_count: ClientCount, minimum_loading: ClientLoading, maximum_loading: ClientLoading
) -> tuple[ClientLoading, ...]:
    if client_count == 1:
        return (minimum_loading,)
    span = maximum_loading - minimum_loading
    denominator = client_count - 1
    return tuple(minimum_loading + (span * index / denominator) for index in range(client_count))


def generate_unit_variance_autoregressive_latent(
    epoch_count: PositiveEpochCount,
    autoregressive_coefficient: LatentAutoregressiveCoefficient,
    seed: SeedValue,
) -> tuple[LatentState, ...]:
    if epoch_count <= 0:
        raise ValueError("autoregressive latent generation requires a positive epoch count")
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    innovation_scale = sqrt(1.0 - (autoregressive_coefficient**2))
    latent = float(generator.standard_normal())
    series: list[LatentState] = [latent]
    for _epoch in range(epoch_count - 1):
        latent = (autoregressive_coefficient * latent) + (
            innovation_scale * float(generator.standard_normal())
        )
        series.append(latent)
    return tuple(series)


def generate_common_mode_scores(
    latent: tuple[LatentState, ...],
    loadings: tuple[ClientLoading, ...],
    noise_standard_deviation: StandardDeviation,
    seed: SeedValue,
) -> tuple[tuple[DetectorScore, ...], ...]:
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    scores: list[tuple[DetectorScore, ...]] = []
    for value in latent:
        epoch_scores = tuple(
            (loading * value) + (noise_standard_deviation * float(generator.standard_normal()))
            for loading in loadings
        )
        scores.append(epoch_scores)
    return tuple(scores)


def marginal_campaign_targets(client_ids: tuple[ClientId, ...]) -> tuple[ClientId, ...]:
    return lexicographic_target_clients(client_ids, 3)


def apply_marginal_score_shift(
    scores: tuple[DetectorScore, ...],
    ordered_client_ids: tuple[ClientId, ...],
    score_shift: ScoreShift,
) -> tuple[DetectorScore, ...]:
    attacked = set(marginal_campaign_targets(ordered_client_ids))
    shifted: list[DetectorScore] = []
    for client_id, score in zip(ordered_client_ids, scores, strict=True):
        if client_id in attacked:
            shifted.append(score + score_shift)
        else:
            shifted.append(score)
    return tuple(shifted)


def gaussian_copula_pair(correlation: Correlation, seed: SeedValue) -> tuple[RankValue, RankValue]:
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    first = float(generator.standard_normal())
    residual_scale = sqrt(1.0 - (correlation**2))
    second = (correlation * first) + (residual_scale * float(generator.standard_normal()))
    return (standard_normal_cdf(first), standard_normal_cdf(second))


def round_half_up(non_negative_count: FractionalClientCount) -> ClientCount:
    if non_negative_count < 0.0:
        raise ValueError("round_half_up is defined for non-negative counts")
    return floor(non_negative_count + 0.5)


def contaminated_outside_count(fraction: Probability, complement_size: ClientCount) -> ClientCount:
    return round_half_up(fraction * complement_size)


def contaminated_outside_clients(
    complement_client_ids: tuple[ClientId, ...], fraction: Probability
) -> tuple[ClientId, ...]:
    ordered = tuple(sorted(complement_client_ids))
    count = contaminated_outside_count(fraction, len(ordered))
    return ordered[:count]


def contaminate_rank(
    rank: RankValue, outside_rank_shift: ScoreShift, rank_clip_epsilon: NumericalFloor
) -> RankValue:
    shifted = rank + outside_rank_shift
    upper = 1.0 - rank_clip_epsilon
    if shifted > upper:
        return upper
    return shifted


def availability_mask(
    client_ids: tuple[ClientId, ...], unavailable_fraction: Probability, seed: SeedValue
) -> tuple[ClientId, ...]:
    generator = np.random.default_rng(thirty_two_bit_seed(seed))
    available: list[ClientId] = []
    stay_probability = 1.0 - unavailable_fraction
    for client_id in client_ids:
        if float(generator.random()) < stay_probability:
            available.append(client_id)
    return tuple(available)


def dropout_coalition_is_active(
    coalition_client_ids: tuple[ClientId, ...],
    available_client_ids: tuple[ClientId, ...],
    selected_client_ids: tuple[ClientId, ...],
    minimum_available_outside_clients: ClientCount,
    minimum_available_outside_fraction: Probability,
) -> Boolean:
    available = set(available_client_ids)
    if any(member not in available for member in coalition_client_ids):
        return False
    complement = tuple(
        client_id for client_id in selected_client_ids if client_id not in set(coalition_client_ids)
    )
    available_outside = tuple(client_id for client_id in complement if client_id in available)
    required = required_outside_client_count(
        len(complement),
        minimum_available_outside_clients,
        minimum_available_outside_fraction,
    )
    return len(available_outside) >= required


def outside_contamination_targets(client_ids: tuple[ClientId, ...]) -> tuple[ClientId, ...]:
    return lexicographic_target_clients(client_ids, 3)


@dataclass(frozen=True)
class SyntheticValidationResult:
    state: ExperimentState
    failed_checks: tuple[ComponentName, ...]


def validate_synthetic_generators(
    loaded: LoadedScientificConfiguration,
) -> SyntheticValidationResult:
    del loaded
    failed: list[ComponentName] = []
    loadings = equally_spaced_loadings(3, 0.0, 1.0)
    if loadings != (0.0, 0.5, 1.0):
        failed.append("common-mode loading grid")
    latent = generate_unit_variance_autoregressive_latent(8, 0.5, 11)
    scores = generate_common_mode_scores(latent, loadings, 0.5, 12)
    if len(scores) != len(latent) or any(len(row) != len(loadings) for row in scores):
        failed.append("common-mode score shape")
    shifted = apply_marginal_score_shift((0.0, 0.0, 0.0), ("a", "b", "c"), 1.0)
    if shifted != (1.0, 1.0, 1.0):
        failed.append("controlled marginal campaign")
    pair = gaussian_copula_pair(0.5, 13)
    if any(rank < 0.0 or rank > 1.0 for rank in pair):
        failed.append("gaussian copula rank range")
    contaminated = contaminated_outside_clients(("a", "b", "c", "d"), 0.5)
    if contaminated != ("a", "b"):
        failed.append("outside contamination selection")
    if not dropout_coalition_is_active(("a",), ("a", "b", "c"), ("a", "b", "c"), 1, 0.5):
        failed.append("dropout active-coalition rule")
    return SyntheticValidationResult(
        state=ExperimentState.COMPLETED if not failed else ExperimentState.INVALID,
        failed_checks=tuple(failed),
    )
