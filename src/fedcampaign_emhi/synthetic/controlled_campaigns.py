from math import sqrt

import numpy as np

from fedcampaign_emhi.domain.types import (
    ClientId,
    Correlation,
    FiniteFloat,
    RankValue,
    ScoreShift,
    SeedValue,
)
from fedcampaign_emhi.emhi.gaussian import standard_normal_cdf
from fedcampaign_emhi.runtime.determinism import thirty_two_bit_seed
from fedcampaign_emhi.synthetic.pure_order import lexicographic_target_clients


def marginal_campaign_targets(client_ids: tuple[ClientId, ...]) -> tuple[ClientId, ...]:
    return lexicographic_target_clients(client_ids, 3)


def pair_relation_targets(client_ids: tuple[ClientId, ...]) -> tuple[ClientId, ...]:
    return lexicographic_target_clients(client_ids, 2)


def single_client_target(client_ids: tuple[ClientId, ...]) -> ClientId:
    return lexicographic_target_clients(client_ids, 1)[0]


def apply_marginal_score_shift(
    scores: tuple[FiniteFloat, ...],
    ordered_client_ids: tuple[ClientId, ...],
    score_shift: ScoreShift,
) -> tuple[FiniteFloat, ...]:
    attacked = set(marginal_campaign_targets(ordered_client_ids))
    shifted: list[FiniteFloat] = []
    for client_id, score in zip(ordered_client_ids, scores, strict=True):
        if client_id in attacked:
            shifted.append(score + score_shift)
        else:
            shifted.append(score)
    return tuple(shifted)


def apply_single_client_score_shift(
    scores: tuple[FiniteFloat, ...],
    ordered_client_ids: tuple[ClientId, ...],
    score_shift: ScoreShift,
) -> tuple[FiniteFloat, ...]:
    attacked = single_client_target(ordered_client_ids)
    shifted: list[FiniteFloat] = []
    for client_id, score in zip(ordered_client_ids, scores, strict=True):
        if client_id == attacked:
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
