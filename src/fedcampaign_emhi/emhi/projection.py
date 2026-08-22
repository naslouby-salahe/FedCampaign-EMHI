from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import (
    BasisSize,
    DesignColumnCount,
    EpochIndexValue,
    FoldCount,
    ProperSubsetDesignShape,
    RecordCount,
)
from fedcampaign_emhi.emhi.basis import tensor_dimension


def proper_subset_design_column_count(
    coalition_order: CoalitionOrder, basis_size: BasisSize
) -> DesignColumnCount:
    if coalition_order is CoalitionOrder.ONE:
        return 1
    if coalition_order is CoalitionOrder.TWO:
        return 1 + (2 * basis_size)
    return 1 + (3 * basis_size) + (3 * (basis_size**2))


def proper_subset_design_shape(
    coalition_order: CoalitionOrder, basis_size: BasisSize
) -> ProperSubsetDesignShape:
    return ProperSubsetDesignShape(
        coalition_order=coalition_order,
        basis_size=basis_size,
        tensor_dimension=tensor_dimension(basis_size, coalition_order),
        design_column_count=proper_subset_design_column_count(coalition_order, basis_size),
    )


def blocked_fold_bounds(
    observation_count: RecordCount, fold_count: FoldCount
) -> tuple[tuple[EpochIndexValue, EpochIndexValue], ...]:
    if observation_count < fold_count:
        raise ValueError("requested fit is unsupported because n is less than k")
    quotient, remainder = divmod(observation_count, fold_count)
    bounds: list[tuple[EpochIndexValue, EpochIndexValue]] = []
    start = 0
    for fold_index in range(fold_count):
        size = quotient + 1 if fold_index < remainder else quotient
        end = start + size
        bounds.append((start, end))
        start = end
    return tuple(bounds)


def blocked_fold_sizes(
    observation_count: RecordCount, fold_count: FoldCount
) -> tuple[RecordCount, ...]:
    return tuple(end - start for start, end in blocked_fold_bounds(observation_count, fold_count))
