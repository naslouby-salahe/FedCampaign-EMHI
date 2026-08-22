from math import sqrt

from scipy.special import erfinv

from fedcampaign_emhi.domain.types import (
    ClientId,
    Correlation,
    FiniteFloat,
    NumericalFloor,
    RankValue,
)
from fedcampaign_emhi.emhi.gaussian import standard_normal_cdf


def lexicographic_vine_order(client_ids: tuple[ClientId, ...]) -> tuple[ClientId, ...]:
    if len(client_ids) != 3:
        raise ValueError("D-vine triples must contain exactly three clients")
    ordered = tuple(sorted(client_ids))
    return ordered


def standard_normal_quantile(rank: RankValue, rank_clip_epsilon: NumericalFloor) -> FiniteFloat:
    lower = rank_clip_epsilon
    upper = 1.0 - rank_clip_epsilon
    clipped = min(max(rank, lower), upper)
    return sqrt(2.0) * float(erfinv((2.0 * clipped) - 1.0))


def gaussian_h_function(
    left_rank: RankValue,
    conditioning_rank: RankValue,
    correlation: Correlation,
    rank_clip_epsilon: NumericalFloor,
) -> RankValue:
    left = standard_normal_quantile(left_rank, rank_clip_epsilon)
    conditioned = standard_normal_quantile(conditioning_rank, rank_clip_epsilon)
    residual_scale = sqrt(1.0 - (correlation**2))
    return standard_normal_cdf((left - (correlation * conditioned)) / residual_scale)
