from collections.abc import Mapping
from dataclasses import dataclass

from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import CoalitionOrder, ContextMethodName, DatasetName, MethodName
from fedcampaign_emhi.domain.types import (
    ClientId,
    EpochIndexValue,
    HistogramBinMass,
    RankReference,
    RankValue,
    RecordCount,
)
from fedcampaign_emhi.emhi.contexts import (
    ContextTrainingRow,
    cap_context_training_rows,
    context_cluster_identity,
    fit_context_centroids,
    outside_context_histogram,
)
from fedcampaign_emhi.emhi.structure import batch_clipped_midrank


@dataclass(frozen=True)
class ComparatorEpochPanel:
    epochs: tuple[EpochIndexValue, ...]
    rows: tuple[tuple[RankValue, ...], ...]
    index_by_epoch: Mapping[EpochIndexValue, RecordCount]


@dataclass(frozen=True)
class ComparatorConditioningModel:
    order: CoalitionOrder
    selected_client_ids: tuple[ClientId, ...]
    centroids: tuple[tuple[HistogramBinMass, ...], ...]
    member_cell_references: tuple[tuple[tuple[RankValue, ...], ...], ...]


CONDITIONED_COMPARATOR_METHODS = frozenset(
    {
        MethodName.CONDITIONAL_PAIR_DEPENDENCE,
        MethodName.EXCLUSION_MATCHED_LANCASTER_TRIPLE,
        MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD,
        MethodName.CONNECTED_INFORMATION_REFERENCE,
        MethodName.CONDITIONAL_LOG_LINEAR_REFERENCE,
    }
)

CONDITIONED_COMPARATOR_ORDERS = {
    MethodName.CONDITIONAL_PAIR_DEPENDENCE: CoalitionOrder.TWO,
    MethodName.EXCLUSION_MATCHED_LANCASTER_TRIPLE: CoalitionOrder.THREE,
    MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD: CoalitionOrder.THREE,
    MethodName.CONNECTED_INFORMATION_REFERENCE: CoalitionOrder.THREE,
    MethodName.CONDITIONAL_LOG_LINEAR_REFERENCE: CoalitionOrder.THREE,
}


def conditioned_comparator_order(method_name: MethodName) -> CoalitionOrder | None:
    return CONDITIONED_COMPARATOR_ORDERS.get(method_name)


def comparator_panel(
    epochs: tuple[EpochIndexValue, ...],
    rows: tuple[tuple[RankValue, ...], ...],
) -> ComparatorEpochPanel:
    if len(epochs) != len(rows):
        raise ValueError("comparator panel epochs and rows must be aligned")
    return ComparatorEpochPanel(
        epochs=epochs,
        rows=rows,
        index_by_epoch={epoch: index for index, epoch in enumerate(epochs)},
    )


def _context_histogram(
    config: ScientificConfig,
    member_count: RecordCount,
    selected_client_ids: tuple[ClientId, ...],
    lag_ranks: tuple[RankValue, ...],
) -> tuple[HistogramBinMass, ...] | None:
    complement_ids = selected_client_ids[member_count:]
    if not complement_ids:
        return None
    lagged = tuple(
        (client_id, rank)
        for client_id, rank in zip(complement_ids, lag_ranks[member_count:], strict=True)
    )
    histogram = outside_context_histogram(
        lagged,
        complement_ids,
        complement_ids,
        config.context.outside_histogram_bin_count,
        config.context.minimum_available_outside_clients,
        config.context.minimum_available_outside_fraction,
    )
    if histogram.abstained:
        return None
    return histogram.bin_mass


def _distance(
    histogram: tuple[HistogramBinMass, ...], centroid: tuple[HistogramBinMass, ...]
) -> HistogramBinMass:
    return sum((left - right) ** 2 for left, right in zip(histogram, centroid, strict=True))


def _nearest_cell(
    histogram: tuple[HistogramBinMass, ...],
    centroids: tuple[tuple[HistogramBinMass, ...], ...],
) -> RecordCount:
    return min(
        range(len(centroids)),
        key=lambda index: _distance(histogram, centroids[index]),
    )


def fit_comparator_conditioning(
    config: ScientificConfig,
    dataset_name: DatasetName,
    panel: ComparatorEpochPanel,
    nuisance_epochs: tuple[EpochIndexValue, ...],
    member_count: RecordCount,
    selected_client_ids: tuple[ClientId, ...],
) -> ComparatorConditioningModel | None:
    if member_count <= 0 or member_count > len(selected_client_ids):
        return None
    training: list[tuple[tuple[HistogramBinMass, ...], EpochIndexValue, tuple[RankValue, ...]]] = []
    for epoch_index in nuisance_epochs:
        row_index = panel.index_by_epoch.get(epoch_index)
        if row_index is None or row_index == 0:
            continue
        histogram = _context_histogram(
            config, member_count, selected_client_ids, panel.rows[row_index - 1]
        )
        if histogram is None:
            continue
        training.append((histogram, epoch_index, panel.rows[row_index]))
    if len(training) < config.context.primary_cell_count:
        return None
    context_rows = tuple(
        ContextTrainingRow(
            dataset=dataset_name,
            coalition_order=CoalitionOrder(member_count),
            coalition_client_ids=selected_client_ids[:member_count],
            epoch_index=epoch_index,
            histogram=histogram,
        )
        for histogram, epoch_index, _ranks in training
    )
    context_seed = config.randomness.context_base_seed
    capped = cap_context_training_rows(
        context_rows,
        context_seed,
        config.context.kmeans.max_fit_rows,
    )
    identity = context_cluster_identity(
        dataset_name,
        CoalitionOrder(member_count),
        ContextMethodName.EXACT_COALITION_EXCLUSION,
        None,
    )
    fitted = fit_context_centroids(
        capped,
        identity,
        config.context.primary_cell_count,
        config.context.kmeans.n_init,
        config.context.kmeans.max_iterations,
        config.context.kmeans.tolerance,
        config.context.kmeans.assignment_tie_tolerance,
        context_seed,
    )
    if fitted is None:
        return None
    references: list[list[list[RankValue]]] = [
        [[] for _member in range(member_count)] for _cell in range(len(fitted.centroids))
    ]
    for histogram, _epoch_index, ranks in training:
        cell = _nearest_cell(histogram, fitted.centroids)
        for member in range(member_count):
            references[cell][member].append(ranks[member])
    sorted_references = tuple(
        tuple(tuple(sorted(references[cell][member])) for member in range(member_count))
        for cell in range(len(references))
    )
    usable_cells = tuple(
        cell
        for cell in range(len(references))
        if all(len(sorted_references[cell][member]) >= 2 for member in range(member_count))
    )
    if not usable_cells:
        return None
    return ComparatorConditioningModel(
        order=CoalitionOrder(member_count),
        selected_client_ids=selected_client_ids,
        centroids=tuple(fitted.centroids[cell] for cell in usable_cells),
        member_cell_references=tuple(sorted_references[cell] for cell in usable_cells),
    )


def condition_epoch_ranks(
    config: ScientificConfig,
    panel: ComparatorEpochPanel,
    epoch_index: EpochIndexValue,
    model: ComparatorConditioningModel,
) -> tuple[RankValue, ...] | None:
    row_index = panel.index_by_epoch.get(epoch_index)
    if row_index is None or row_index == 0:
        return None
    member_count = len(model.member_cell_references[0])
    histogram = _context_histogram(
        config,
        member_count,
        model.selected_client_ids,
        panel.rows[row_index - 1],
    )
    if histogram is None:
        return None
    cell = _nearest_cell(histogram, model.centroids)
    row = panel.rows[row_index]
    return tuple(
        batch_clipped_midrank(
            (row[member],),
            RankReference(scores=model.member_cell_references[cell][member]),
            config.context.rank_clip_epsilon,
        )[0]
        for member in range(member_count)
    )
