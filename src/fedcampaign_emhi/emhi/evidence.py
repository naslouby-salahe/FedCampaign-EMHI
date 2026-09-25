from dataclasses import dataclass
from math import exp, sqrt

import numpy as np

from fedcampaign_emhi.domain.types import (
    BettingLambda,
    CompensatorValue,
    EvidenceClipBound,
    EvidenceFactor,
    EvidenceStatistic,
    NumericalFloor,
    OperationalNormReference,
    Quantile,
    RecordCount,
    SignedDirectionCoordinate,
    StandardizedAtomCoordinate,
)

OPERATIONAL_EVIDENCE_COMPENSATOR = 0.125


@dataclass(frozen=True)
class CumulativeAtomState:
    running_sum: tuple[StandardizedAtomCoordinate, ...]
    epoch_count: RecordCount


def initial_cumulative_atom_state() -> CumulativeAtomState:
    return CumulativeAtomState(running_sum=(), epoch_count=0)


def advance_cumulative_atom_state(
    previous: CumulativeAtomState,
    atom: tuple[StandardizedAtomCoordinate, ...],
) -> CumulativeAtomState:
    base = previous.running_sum if previous.epoch_count else tuple(0.0 for _ in atom)
    if len(base) != len(atom):
        raise ValueError("cumulative atom state dimension mismatch")
    updated_sum = tuple(prior + value for prior, value in zip(base, atom, strict=True))
    return CumulativeAtomState(running_sum=updated_sum, epoch_count=previous.epoch_count + 1)


def cumulative_operational_evidence_factor(
    state: CumulativeAtomState,
    atom: tuple[StandardizedAtomCoordinate, ...],
    reference_quantile: OperationalNormReference,
    norm_reference_floor: NumericalFloor,
    clip_bound: EvidenceClipBound,
    bet_lambda: BettingLambda,
) -> tuple[EvidenceFactor, CumulativeAtomState]:
    updated = advance_cumulative_atom_state(state, atom)
    normalized_sum = tuple(value / sqrt(updated.epoch_count) for value in updated.running_sum)
    factor = operational_evidence_factor(
        normalized_sum, reference_quantile, norm_reference_floor, clip_bound, bet_lambda
    )
    return factor, updated


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


def operational_norm_reference_quantile(
    standardized_atoms: tuple[tuple[StandardizedAtomCoordinate, ...], ...], quantile: Quantile
) -> OperationalNormReference:
    if not standardized_atoms:
        raise ValueError("operational norm reference requires cross-fitted innovations")
    norms = tuple(euclidean_norm(atom) for atom in standardized_atoms)
    array = np.asarray(norms, dtype=np.float64)
    return float(np.quantile(array, quantile))


def within_order_aggregate(factors: tuple[EvidenceFactor, ...]) -> EvidenceFactor:
    if not factors:
        return 1.0
    return sum(factors) / len(factors)


def across_order_aggregate(order_factors: tuple[EvidenceFactor, ...]) -> EvidenceFactor:
    if not order_factors:
        raise ValueError("enabled order set must be non-empty")
    return sum(order_factors) / len(order_factors)
