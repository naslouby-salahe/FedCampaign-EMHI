from dataclasses import dataclass
from math import sqrt

from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import (
    Boolean,
    ClientCount,
    FiniteFloat,
    NumericalFloor,
    Probability,
    RecordCount,
)


@dataclass(frozen=True)
class PairedAtomMetrics:
    nrmse: FiniteFloat
    cosine_similarity: FiniteFloat


def paired_atom_metrics(
    emhi_atoms: tuple[tuple[FiniteFloat, ...], ...],
    hofd_atoms: tuple[tuple[FiniteFloat, ...], ...],
    denominator_floor: NumericalFloor,
) -> PairedAtomMetrics:
    if not emhi_atoms or len(emhi_atoms) != len(hofd_atoms):
        raise ValueError("paired atom metrics require aligned nonempty rows")
    if any(len(emhi) != len(hofd) for emhi, hofd in zip(emhi_atoms, hofd_atoms, strict=True)):
        raise ValueError("paired atom vectors must have equal dimensions")
    squared_error = sum(
        sum((emhi - hofd) ** 2 for emhi, hofd in zip(left, right, strict=True))
        for left, right in zip(emhi_atoms, hofd_atoms, strict=True)
    )
    squared_reference = sum(sum(value * value for value in row) for row in emhi_atoms)
    inner_product = sum(
        sum(emhi * hofd for emhi, hofd in zip(left, right, strict=True))
        for left, right in zip(emhi_atoms, hofd_atoms, strict=True)
    )
    squared_hofd = sum(sum(value * value for value in row) for row in hofd_atoms)
    return PairedAtomMetrics(
        nrmse=sqrt(squared_error / len(emhi_atoms))
        / max(sqrt(squared_reference / len(emhi_atoms)), denominator_floor),
        cosine_similarity=inner_product
        / max(sqrt(squared_reference) * sqrt(squared_hofd), denominator_floor),
    )


def target_coalition_for_order(order: CoalitionOrder, client_count: ClientCount) -> RecordCount:
    order_size = int(order)
    if order_size > client_count:
        raise ValueError("target coalition exceeds the selected client count")
    target: RecordCount = order_size
    return target


def nrmse_equivalence_criterion(nrmse_upper: FiniteFloat, margin: FiniteFloat) -> Boolean:
    return nrmse_upper < margin


def cosine_equivalence_criterion(mean_cosine: FiniteFloat, minimum: FiniteFloat) -> Boolean:
    return mean_cosine >= minimum


def stopping_time_equivalence_criterion(
    ci_lower: FiniteFloat,
    ci_upper: FiniteFloat,
    interval_lower: FiniteFloat,
    interval_upper: FiniteFloat,
) -> Boolean:
    return ci_lower >= interval_lower and ci_upper <= interval_upper


def pfa_prerequisite_criterion(null_pfa_upper: Probability, target_pfa: Probability) -> Boolean:
    return null_pfa_upper <= target_pfa
