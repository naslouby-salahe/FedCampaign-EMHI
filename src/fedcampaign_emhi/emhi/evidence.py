from math import exp, sqrt

from fedcampaign_emhi.domain.types import EvidenceFactor, FiniteFloat, NumericalFloor, PositiveFloat


def clip_statistic(statistic: FiniteFloat, clip_bound: PositiveFloat) -> FiniteFloat:
    if statistic > clip_bound:
        return clip_bound
    if statistic < -clip_bound:
        return -clip_bound
    return statistic


def signed_theorem_compensator(clip_bound: PositiveFloat, bet_lambda: PositiveFloat) -> FiniteFloat:
    return (bet_lambda**2) * ((2.0 * clip_bound) ** 2) / 8.0


def evidence_factor(
    statistic: FiniteFloat, clip_bound: PositiveFloat, bet_lambda: PositiveFloat
) -> EvidenceFactor:
    clipped = clip_statistic(statistic, clip_bound)
    return exp(bet_lambda * clipped - signed_theorem_compensator(clip_bound, bet_lambda))


def signed_evidence_factor(
    signed_statistic: FiniteFloat,
    clip_bound: PositiveFloat,
    bet_lambda: PositiveFloat,
) -> EvidenceFactor:
    return evidence_factor(signed_statistic, clip_bound, bet_lambda)


def euclidean_norm(coordinates: tuple[FiniteFloat, ...]) -> FiniteFloat:
    return sqrt(sum(coordinate * coordinate for coordinate in coordinates))


def operational_norm_statistic(
    coordinates: tuple[FiniteFloat, ...],
    reference_quantile: FiniteFloat,
    norm_reference_floor: NumericalFloor,
    clip_bound: PositiveFloat,
) -> FiniteFloat:
    scale = max(reference_quantile, norm_reference_floor)
    return clip_statistic((euclidean_norm(coordinates) / scale) - 1.0, clip_bound)


def operational_evidence_factor(
    coordinates: tuple[FiniteFloat, ...],
    reference_quantile: FiniteFloat,
    norm_reference_floor: NumericalFloor,
    clip_bound: PositiveFloat,
    bet_lambda: PositiveFloat,
) -> EvidenceFactor:
    statistic = operational_norm_statistic(
        coordinates, reference_quantile, norm_reference_floor, clip_bound
    )
    return evidence_factor(statistic, clip_bound, bet_lambda)


def within_order_aggregate(factors: tuple[EvidenceFactor, ...]) -> EvidenceFactor:
    if not factors:
        return 1.0
    return sum(factors) / len(factors)


def across_order_aggregate(order_factors: tuple[EvidenceFactor, ...]) -> EvidenceFactor:
    if not order_factors:
        raise ValueError("enabled order set must be non-empty")
    return sum(order_factors) / len(order_factors)
