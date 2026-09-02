from math import exp, sqrt

import numpy as np

from fedcampaign_emhi.domain.enums import EvidencePath
from fedcampaign_emhi.domain.types import (
    BettingLambda,
    Boolean,
    CompensatorValue,
    EffectCoefficient,
    EvidenceClipBound,
    EvidenceFactor,
    EvidenceStatistic,
    NumericalFloor,
    OperationalNormReference,
    Quantile,
    SignedDirectionCoordinate,
    StandardizedAtomCoordinate,
    TensorDimension,
)

OPERATIONAL_EVIDENCE_COMPENSATOR = 0.125
LOCKED_SIGNED_CLIP_BOUND = 1.0
LOCKED_SIGNED_BET_LAMBDA = 0.5
SIGNED_NULL_EXPECTATION_UPPER_BOUND = 0.0


def clip_statistic(
    statistic: EvidenceStatistic, clip_bound: EvidenceClipBound
) -> EvidenceStatistic:
    if statistic > clip_bound:
        return clip_bound
    if statistic < -clip_bound:
        return -clip_bound
    return statistic


def signed_theorem_compensator(
    clip_bound: EvidenceClipBound, bet_lambda: BettingLambda
) -> CompensatorValue:
    return (bet_lambda**2) * ((2.0 * clip_bound) ** 2) / 8.0


def evidence_factor(
    statistic: EvidenceStatistic, clip_bound: EvidenceClipBound, bet_lambda: BettingLambda
) -> EvidenceFactor:
    clipped = clip_statistic(statistic, clip_bound)
    return exp(bet_lambda * clipped - signed_theorem_compensator(clip_bound, bet_lambda))


def signed_evidence_factor(
    signed_statistic: EvidenceStatistic,
    clip_bound: EvidenceClipBound,
    bet_lambda: BettingLambda,
) -> EvidenceFactor:
    return evidence_factor(signed_statistic, clip_bound, bet_lambda)


def euclidean_norm(coordinates: tuple[StandardizedAtomCoordinate, ...]) -> OperationalNormReference:
    return sqrt(sum(coordinate * coordinate for coordinate in coordinates))


def operational_norm_statistic(
    coordinates: tuple[StandardizedAtomCoordinate, ...],
    reference_quantile: OperationalNormReference,
    norm_reference_floor: NumericalFloor,
    clip_bound: EvidenceClipBound,
) -> EvidenceStatistic:
    scale = max(reference_quantile, norm_reference_floor)
    return clip_statistic((euclidean_norm(coordinates) / scale) - 1.0, clip_bound)


def operational_evidence_factor(
    coordinates: tuple[StandardizedAtomCoordinate, ...],
    reference_quantile: OperationalNormReference,
    norm_reference_floor: NumericalFloor,
    clip_bound: EvidenceClipBound,
    bet_lambda: BettingLambda,
) -> EvidenceFactor:
    statistic = operational_norm_statistic(
        coordinates, reference_quantile, norm_reference_floor, clip_bound
    )
    return exp(bet_lambda * statistic - OPERATIONAL_EVIDENCE_COMPENSATOR)


def signed_direction_is_fixed_before_evaluation(
    direction: tuple[SignedDirectionCoordinate, ...],
) -> Boolean:
    return any(coordinate > 0.0 or coordinate < 0.0 for coordinate in direction)


def polynomial_signed_direction(
    tensor_size: TensorDimension, generator_coefficient: EffectCoefficient
) -> tuple[SignedDirectionCoordinate, ...]:
    if tensor_size <= 0:
        raise ValueError("tensor_size must be positive")
    if not (generator_coefficient > 0.0 or generator_coefficient < 0.0):
        raise ValueError("signed evidence requires a nonzero predeclared generator coefficient")
    sign: SignedDirectionCoordinate = 1.0 if generator_coefficient > 0.0 else -1.0
    return tuple(sign if index == 0 else 0.0 for index in range(tensor_size))


def signed_statistic(
    standardized_atom: tuple[StandardizedAtomCoordinate, ...],
    direction: tuple[SignedDirectionCoordinate, ...],
    clip_bound: EvidenceClipBound,
) -> EvidenceStatistic:
    if len(standardized_atom) != len(direction):
        raise ValueError("standardized atom and signed direction must be aligned")
    projected = sum(
        coordinate * loading
        for coordinate, loading in zip(standardized_atom, direction, strict=True)
    )
    return clip_statistic(projected, clip_bound)


def signed_conditional_null_holds(expected_statistic: EvidenceStatistic) -> Boolean:
    return expected_statistic <= SIGNED_NULL_EXPECTATION_UPPER_BOUND


def conditional_e_detector_path() -> EvidencePath:
    return EvidencePath.SIGNED_THEOREM


def primary_real_data_evidence_path() -> EvidencePath:
    return EvidencePath.OPERATIONAL_NORM


def operational_norm_reference_quantile(
    standardized_atoms: tuple[tuple[StandardizedAtomCoordinate, ...], ...], quantile: Quantile
) -> OperationalNormReference:
    if not standardized_atoms:
        raise ValueError("operational norm reference requires cross-fitted innovations")
    norms = tuple(euclidean_norm(atom) for atom in standardized_atoms)
    array = np.asarray(norms, dtype=np.float64)
    return float(np.quantile(array, quantile))


def locked_signed_compensator() -> EvidenceStatistic:
    return signed_theorem_compensator(LOCKED_SIGNED_CLIP_BOUND, LOCKED_SIGNED_BET_LAMBDA)


def within_order_aggregate(factors: tuple[EvidenceFactor, ...]) -> EvidenceFactor:
    if not factors:
        return 1.0
    return sum(factors) / len(factors)


def across_order_aggregate(order_factors: tuple[EvidenceFactor, ...]) -> EvidenceFactor:
    if not order_factors:
        raise ValueError("enabled order set must be non-empty")
    return sum(order_factors) / len(order_factors)
