from collections import UserDict

from fedcampaign_emhi.artifacts.records import (
    CoalitionFitRecord,
    ConditionalRankReferenceRecord,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
    EMHIFitArtifactRecord,
    MarginalRankArtifactRecord,
    OrderContextFitRecord,
    ProjectionCellFitRecord,
)
from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ContextMethodName,
    MethodName,
    PartitionRole,
    SupportState,
)
from fedcampaign_emhi.domain.types import (
    BasisSize,
    BinIndex,
    Boolean,
    CellCount,
    ClientId,
    CoalitionMembers,
    ContextTrainingRow,
    CrossFittedInnovationCalibration,
    EpochIndexValue,
    FiniteFloat,
    FoldCount,
    MaterialDependencyFingerprint,
    NumericalFloor,
    NumericalTolerance,
    RankReference,
    RankValue,
    RecordCount,
    RidgePenalty,
    SeedDerivationIdentity,
    SeedValue,
)
from fedcampaign_emhi.emhi.basis import tensor_representation
from fedcampaign_emhi.emhi.coalitions import enumerate_coalitions
from fedcampaign_emhi.emhi.contexts import (
    NO_OUTSIDE_CONTEXT_CELL_COUNT,
    assign_context_cell,
    cap_context_training_rows,
    context_cluster_identity,
    exact_exclusion_members,
    fit_context_centroids,
    inclusive_context_members,
    leave_one_out_context_members,
    local_history_context_member_ranks,
    minimum_support_epochs_for_order,
    outside_context_histogram,
    partial_coalition_context_members,
    shuffled_outside_context_lag_lookup,
)
from fedcampaign_emhi.emhi.evidence import operational_norm_reference_quantile
from fedcampaign_emhi.emhi.innovations import (
    center_and_scale_atom,
    projection_residual,
    sample_mean,
    sample_standard_deviation,
    unsupported_context_observation_count,
)
from fedcampaign_emhi.emhi.projection import (
    blocked_fit_is_supported,
    blocked_fold_bounds,
    fold_size_weighted_mse,
    proper_subset_design_row,
    ridge_coefficient_matrix,
    select_ridge_penalty,
)
from fedcampaign_emhi.emhi.ranks import (
    build_marginal_rank_artifact,
    coalition_conditioned_residual_rank,
    rank_at_epoch,
)
from fedcampaign_emhi.runtime.determinism import derive_component_seed

type FoldRankCache = UserDict[tuple[RecordCount, RecordCount], MarginalRankArtifactRecord]
type OrderContextCache = UserDict[
    tuple[RecordCount, RecordCount, CoalitionOrder], OrderContextFitRecord
]


def fold_observation_indexes(
    observation_count: RecordCount, fold_count: FoldCount
) -> tuple[tuple[tuple[RecordCount, ...], tuple[RecordCount, ...]], ...]:
    bounds = blocked_fold_bounds(observation_count, fold_count)
    splits: list[tuple[tuple[RecordCount, ...], tuple[RecordCount, ...]]] = []
    all_indexes = tuple(range(observation_count))
    for start, end in bounds:
        held = tuple(range(start, end))
        training = tuple(index for index in all_indexes if index < start or index >= end)
        splits.append((training, held))
    return tuple(splits)


def select_rows(
    rows: tuple[tuple[FiniteFloat, ...], ...], indexes: tuple[RecordCount, ...]
) -> tuple[tuple[FiniteFloat, ...], ...]:
    return tuple(rows[index] for index in indexes)


def residual_mean_square(residuals: tuple[tuple[FiniteFloat, ...], ...]) -> FiniteFloat:
    if not residuals:
        raise ValueError("residual mean square requires held-fold observations")
    total = 0.0
    for residual in residuals:
        total += sum(coordinate * coordinate for coordinate in residual)
    return total / len(residuals)


def cross_validated_ridge_penalty(
    design_rows: tuple[tuple[FiniteFloat, ...], ...],
    tensors: tuple[tuple[FiniteFloat, ...], ...],
    candidates: tuple[RidgePenalty, ...],
    fold_count: FoldCount,
    tie_tolerance: NumericalTolerance,
    svd_relative_cutoff: NumericalFloor,
) -> RidgePenalty | None:
    observation_count = len(design_rows)
    if not blocked_fit_is_supported(observation_count, fold_count):
        return None
    splits = fold_observation_indexes(observation_count, fold_count)
    weighted: list[FiniteFloat] = []
    sizes = tuple(len(held) for _training, held in splits)
    for penalty in candidates:
        fold_mses: list[FiniteFloat] = []
        for training, held in splits:
            coefficients = ridge_coefficient_matrix(
                select_rows(design_rows, training),
                select_rows(tensors, training),
                penalty,
                svd_relative_cutoff,
            )
            held_residuals = tuple(
                projection_residual(tensors[index], coefficients, design_rows[index])
                for index in held
            )
            fold_mses.append(residual_mean_square(held_residuals))
        weighted.append(fold_size_weighted_mse(tuple(fold_mses), sizes))
    return select_ridge_penalty(candidates, tuple(weighted), tie_tolerance)


def held_fold_innovations(
    design_rows: tuple[tuple[FiniteFloat, ...], ...],
    tensors: tuple[tuple[FiniteFloat, ...], ...],
    fold_count: FoldCount,
    ridge_penalty: RidgePenalty,
    svd_relative_cutoff: NumericalFloor,
) -> tuple[tuple[FiniteFloat, ...], ...] | None:
    observation_count = len(design_rows)
    if not blocked_fit_is_supported(observation_count, fold_count):
        return None
    collected: list[tuple[FiniteFloat, ...]] = []
    for training, held in fold_observation_indexes(observation_count, fold_count):
        coefficients = ridge_coefficient_matrix(
            select_rows(design_rows, training),
            select_rows(tensors, training),
            ridge_penalty,
            svd_relative_cutoff,
        )
        for index in held:
            collected.append(projection_residual(tensors[index], coefficients, design_rows[index]))
    return tuple(collected)


def moments_from_held_fold_innovations(
    innovations: tuple[tuple[FiniteFloat, ...], ...],
) -> tuple[tuple[FiniteFloat, ...], tuple[FiniteFloat, ...]] | None:
    if unsupported_context_observation_count(len(innovations)):
        return None
    dimension = len(innovations[0])
    means: list[FiniteFloat] = []
    deviations: list[FiniteFloat] = []
    for coordinate_index in range(dimension):
        series = tuple(innovation[coordinate_index] for innovation in innovations)
        means.append(sample_mean(series))
        deviations.append(sample_standard_deviation(series))
    return tuple(means), tuple(deviations)


def calibrate_innovations_on_nuisance_fit(
    design_rows: tuple[tuple[FiniteFloat, ...], ...],
    tensors: tuple[tuple[FiniteFloat, ...], ...],
    candidates: tuple[RidgePenalty, ...],
    fold_count: FoldCount,
    tie_tolerance: NumericalTolerance,
    svd_relative_cutoff: NumericalFloor,
    scale_floor: NumericalFloor,
) -> CrossFittedInnovationCalibration | None:
    if len(design_rows) != len(tensors):
        raise ValueError("design_rows and tensors must be aligned")
    selected = cross_validated_ridge_penalty(
        design_rows, tensors, candidates, fold_count, tie_tolerance, svd_relative_cutoff
    )
    if selected is None:
        return None
    innovations = held_fold_innovations(
        design_rows, tensors, fold_count, selected, svd_relative_cutoff
    )
    if innovations is None:
        return None
    moments = moments_from_held_fold_innovations(innovations)
    if moments is None:
        return None
    means, deviations = moments
    complete_coefficients = ridge_coefficient_matrix(
        design_rows, tensors, selected, svd_relative_cutoff
    )
    standardized = tuple(
        center_and_scale_atom(atom, means, deviations, scale_floor) for atom in innovations
    )
    return CrossFittedInnovationCalibration(
        held_fold_innovations=innovations,
        coordinate_means=means,
        coordinate_deviations=deviations,
        standardized_held_fold_innovations=standardized,
        complete_nuisance_coefficients=complete_coefficients,
        selected_ridge_penalty=selected,
    )


def _context_members(
    context_method: ContextMethodName,
    selected_client_ids: tuple[ClientId, ...],
    coalition_client_ids: tuple[ClientId, ...],
) -> tuple[ClientId, ...]:
    if context_method in {
        ContextMethodName.EXACT_COALITION_EXCLUSION,
        ContextMethodName.FORCED_NO_ABSTENTION,
        ContextMethodName.SHUFFLED_OUTSIDE_CONTEXT,
    }:
        return exact_exclusion_members(selected_client_ids, coalition_client_ids)
    if context_method is ContextMethodName.INCLUSIVE_CONTEXT:
        return inclusive_context_members(selected_client_ids, coalition_client_ids)
    if context_method is ContextMethodName.LEAVE_ONE_OUT_INSUFFICIENT_EXCLUSION:
        return leave_one_out_context_members(selected_client_ids, coalition_client_ids)
    if context_method is ContextMethodName.PARTIAL_COALITION_EXCLUSION:
        if len(coalition_client_ids) == 1:
            return exact_exclusion_members(selected_client_ids, coalition_client_ids)
        return partial_coalition_context_members(selected_client_ids, coalition_client_ids)
    if context_method is ContextMethodName.LOCAL_HISTORY_ONLY_CONTEXT:
        return tuple(sorted(coalition_client_ids))
    if context_method is ContextMethodName.NO_OUTSIDE_CONTEXT:
        return ()
    raise ValueError(
        f"context method {context_method.value} requires a specialized execution route"
    )


def context_seed_for_order(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    coalition_order: CoalitionOrder,
    context_method: ContextMethodName,
) -> SeedValue:
    return derive_component_seed(
        SeedDerivationIdentity(
            base_seed=config.randomness.context_base_seed,
            component_name=f"{context_method.value}-order-{int(coalition_order)}-root-{ranks.root_seed}",
            dataset=ranks.dataset_name,
            client_ids=(),
            coalition_ids=(),
            condition_coordinates=(),
        )
    )


def _context_row(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    coalition: CoalitionMembers,
    epoch_index: EpochIndexValue,
    context_method: ContextMethodName,
    permitted_lag_epochs: tuple[EpochIndexValue, ...] | None,
    *,
    shuffled_lag_epoch: EpochIndexValue | None = None,
) -> ContextTrainingRow | None:
    if context_method is ContextMethodName.NO_OUTSIDE_CONTEXT:
        return ContextTrainingRow(
            dataset=ranks.dataset_name,
            coalition_order=coalition.order,
            coalition_client_ids=coalition.client_ids,
            epoch_index=epoch_index,
            histogram=(1.0,),
        )
    if context_method is ContextMethodName.SHUFFLED_OUTSIDE_CONTEXT:
        if shuffled_lag_epoch is None:
            raise ValueError("shuffled outside context requires a precomputed lag lookup")
        lagged_epoch = shuffled_lag_epoch
    else:
        lagged_epoch = epoch_index - config.context.outside_lag_epochs
    if permitted_lag_epochs is not None and lagged_epoch not in permitted_lag_epochs:
        return None
    members = _context_members(context_method, ranks.selected_client_ids, coalition.client_ids)
    lagged = tuple(
        (client_id, rank)
        for client_id in members
        for rank in (rank_at_epoch(ranks, client_id, lagged_epoch),)
        if rank is not None
    )
    available = tuple(client_id for client_id, _rank in lagged)
    if context_method is ContextMethodName.LOCAL_HISTORY_ONLY_CONTEXT:
        member_ranks = local_history_context_member_ranks(coalition.client_ids, lagged)
        if not member_ranks:
            return None
    histogram = outside_context_histogram(
        lagged,
        available,
        members,
        config.context.outside_histogram_bin_count,
        config.context.minimum_available_outside_clients,
        config.context.minimum_available_outside_fraction,
    )
    if histogram.abstained:
        return None
    return ContextTrainingRow(
        dataset=ranks.dataset_name,
        coalition_order=coalition.order,
        coalition_client_ids=coalition.client_ids,
        epoch_index=epoch_index,
        histogram=histogram.bin_mass,
    )


def _minimum_support(config: ScientificConfig, coalition_order: CoalitionOrder) -> RecordCount:
    minimum = config.context.minimum_support_epochs
    return minimum_support_epochs_for_order(
        coalition_order,
        minimum.order_one,
        minimum.order_two,
        minimum.order_three,
    )


def _fit_order_context(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    coalitions: tuple[CoalitionMembers, ...],
    nuisance_epochs: tuple[EpochIndexValue, ...],
    coalition_order: CoalitionOrder,
    context_method: ContextMethodName,
    cell_count: CellCount,
    permitted_lag_epochs: tuple[EpochIndexValue, ...] | None,
) -> OrderContextFitRecord:
    if context_method is ContextMethodName.NO_OUTSIDE_CONTEXT:
        return OrderContextFitRecord(
            coalition_order=coalition_order,
            context_method=context_method,
            centroids=((1.0,),),
            state=SupportState.SUPPORTED,
        )
    context_seed = context_seed_for_order(config, ranks, coalition_order, context_method)
    lag_lookup = (
        shuffled_outside_context_lag_lookup(
            nuisance_epochs,
            PartitionRole.NUISANCE_FIT,
            config.context.outside_lag_epochs,
            context_seed,
        )
        if context_method is ContextMethodName.SHUFFLED_OUTSIDE_CONTEXT
        else None
    )
    rows = tuple(
        row
        for coalition in coalitions
        if coalition.order is coalition_order
        for epoch_index in nuisance_epochs
        for row in (
            _context_row(
                config,
                ranks,
                coalition,
                epoch_index,
                context_method,
                permitted_lag_epochs,
                shuffled_lag_epoch=None if lag_lookup is None else lag_lookup[epoch_index],
            ),
        )
        if row is not None
    )
    capped = cap_context_training_rows(rows, context_seed, config.context.kmeans.max_fit_rows)
    identity = context_cluster_identity(
        ranks.dataset_name,
        coalition_order,
        context_method,
        ranks.root_seed,
    )
    centroids = fit_context_centroids(
        capped,
        identity,
        cell_count,
        config.context.kmeans.n_init,
        config.context.kmeans.max_iterations,
        config.context.kmeans.tolerance,
        config.context.kmeans.assignment_tie_tolerance,
        context_seed,
    )
    if centroids is None:
        return OrderContextFitRecord(
            coalition_order=coalition_order,
            context_method=context_method,
            centroids=(),
            state=SupportState.NOT_TESTED,
        )
    return OrderContextFitRecord(
        coalition_order=coalition_order,
        context_method=context_method,
        centroids=centroids.centroids,
        state=SupportState.SUPPORTED,
    )


def _coalition_cell_epochs(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    coalition: CoalitionMembers,
    nuisance_epochs: tuple[EpochIndexValue, ...],
    centroids: tuple[tuple[FiniteFloat, ...], ...],
    context_cell: BinIndex,
    context_method: ContextMethodName,
    permitted_lag_epochs: tuple[EpochIndexValue, ...] | None,
) -> tuple[EpochIndexValue, ...]:
    if context_method is ContextMethodName.NO_OUTSIDE_CONTEXT:
        return nuisance_epochs
    lag_lookup = (
        shuffled_outside_context_lag_lookup(
            nuisance_epochs,
            PartitionRole.NUISANCE_FIT,
            config.context.outside_lag_epochs,
            context_seed_for_order(config, ranks, coalition.order, context_method),
        )
        if context_method is ContextMethodName.SHUFFLED_OUTSIDE_CONTEXT
        else None
    )
    selected: list[EpochIndexValue] = []
    for epoch_index in nuisance_epochs:
        row = _context_row(
            config,
            ranks,
            coalition,
            epoch_index,
            context_method,
            permitted_lag_epochs,
            shuffled_lag_epoch=None if lag_lookup is None else lag_lookup[epoch_index],
        )
        if row is None:
            continue
        assigned = assign_context_cell(
            row.histogram,
            centroids,
            config.context.kmeans.assignment_tie_tolerance,
        )
        if assigned == context_cell:
            selected.append(epoch_index)
    return tuple(selected)


def _conditional_rank_references(
    ranks: MarginalRankArtifactRecord,
    coalition: CoalitionMembers,
    context_cell: BinIndex,
    epochs: tuple[EpochIndexValue, ...],
) -> tuple[ConditionalRankReferenceRecord, ...]:
    return tuple(
        ConditionalRankReferenceRecord(
            client_id=client_id,
            context_cell=context_cell,
            reference_ranks=tuple(
                rank
                for epoch_index in epochs
                for rank in (rank_at_epoch(ranks, client_id, epoch_index),)
                if rank is not None
            ),
        )
        for client_id in coalition.client_ids
    )


def _conditioned_member_ranks(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    coalition: CoalitionMembers,
    epoch_index: EpochIndexValue,
    references: tuple[ConditionalRankReferenceRecord, ...],
) -> tuple[RankValue, ...] | None:
    conditioned: list[RankValue] = []
    for client_id in coalition.client_ids:
        marginal = rank_at_epoch(ranks, client_id, epoch_index)
        reference = next(
            (item for item in references if item.client_id == client_id and item.reference_ranks),
            None,
        )
        if marginal is None or reference is None:
            return None
        conditioned.append(
            coalition_conditioned_residual_rank(
                marginal,
                RankReference(scores=reference.reference_ranks),
                config.context.rank_clip_epsilon,
            )
        )
    return tuple(conditioned)


def _conditioned_rows(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    coalition: CoalitionMembers,
    epochs: tuple[EpochIndexValue, ...],
    references: tuple[ConditionalRankReferenceRecord, ...],
) -> tuple[tuple[RankValue, ...], ...]:
    return tuple(
        conditioned
        for epoch_index in epochs
        for conditioned in (
            _conditioned_member_ranks(config, ranks, coalition, epoch_index, references),
        )
        if conditioned is not None
    )


def _design_and_tensors(
    rows: tuple[tuple[RankValue, ...], ...],
    basis_size: BasisSize,
) -> tuple[tuple[tuple[FiniteFloat, ...], ...], tuple[tuple[FiniteFloat, ...], ...]]:
    return (
        tuple(proper_subset_design_row(row, basis_size) for row in rows),
        tuple(tensor_representation(row, basis_size) for row in rows),
    )


def _cross_fitted_cell_statistics(
    config: ScientificConfig,
    scores: DetectorScoreArtifactRecord,
    split: DatasetSplitRecord,
    coalitions: tuple[CoalitionMembers, ...],
    coalition: CoalitionMembers,
    context_cell: BinIndex,
    context_method: ContextMethodName,
    cell_count: CellCount,
    basis_size: BasisSize,
    purification_enabled: Boolean,
    forced_no_abstention: Boolean,
    ridge_candidates: tuple[RidgePenalty, ...],
    fold_rank_cache: FoldRankCache,
    order_context_cache: OrderContextCache,
) -> tuple[tuple[FiniteFloat, ...], tuple[FiniteFloat, ...], FiniteFloat] | None:
    nuisance_epochs = split.nuisance_fit_epochs
    fold_count = config.context.nuisance_crossfit.fold_count
    if len(nuisance_epochs) < fold_count:
        return None
    held_innovations: list[tuple[FiniteFloat, ...]] = []
    for start, end in blocked_fold_bounds(len(nuisance_epochs), fold_count):
        held_epochs = nuisance_epochs[start:end]
        training_epochs = nuisance_epochs[:start] + nuisance_epochs[end:]
        fold_key = (start, end)
        fold_ranks = fold_rank_cache.get(fold_key)
        if fold_ranks is None:
            fold_ranks = build_marginal_rank_artifact(
                scores,
                training_epochs,
                config.context.rank_clip_epsilon,
                scores.dependency_fingerprint,
            )
            fold_rank_cache[fold_key] = fold_ranks
        order_context_key = (start, end, coalition.order)
        order_context = order_context_cache.get(order_context_key)
        if order_context is None:
            order_context = _fit_order_context(
                config,
                fold_ranks,
                coalitions,
                training_epochs,
                coalition.order,
                context_method,
                cell_count,
                training_epochs,
            )
            order_context_cache[order_context_key] = order_context
        if order_context.state is not SupportState.SUPPORTED:
            continue
        if context_cell >= len(order_context.centroids):
            continue
        training_cell_epochs = _coalition_cell_epochs(
            config,
            fold_ranks,
            coalition,
            training_epochs,
            order_context.centroids,
            context_cell,
            context_method,
            training_epochs,
        )
        if len(training_cell_epochs) < _minimum_support(config, coalition.order):
            if not forced_no_abstention:
                continue
            training_cell_epochs = training_epochs
        references = _conditional_rank_references(
            fold_ranks,
            coalition,
            context_cell,
            training_cell_epochs,
        )
        training_rows = _conditioned_rows(
            config,
            fold_ranks,
            coalition,
            training_cell_epochs,
            references,
        )
        design_rows, tensors = _design_and_tensors(training_rows, basis_size)
        calibration = None
        if purification_enabled:
            calibration = calibrate_innovations_on_nuisance_fit(
                design_rows,
                tensors,
                ridge_candidates,
                config.projection.cross_validation.fold_count,
                config.projection.selection_tie_tolerance_mse,
                config.projection.zero_ridge_svd_relative_cutoff,
                config.projection.atom_scale_floor,
            )
            if calibration is None:
                continue
        held_lag_lookup = (
            shuffled_outside_context_lag_lookup(
                held_epochs,
                PartitionRole.NUISANCE_FIT,
                config.context.outside_lag_epochs,
                context_seed_for_order(config, fold_ranks, coalition.order, context_method),
            )
            if context_method is ContextMethodName.SHUFFLED_OUTSIDE_CONTEXT
            else None
        )
        for epoch_index in held_epochs:
            row = _context_row(
                config,
                fold_ranks,
                coalition,
                epoch_index,
                context_method,
                None,
                shuffled_lag_epoch=(
                    None if held_lag_lookup is None else held_lag_lookup[epoch_index]
                ),
            )
            if row is None:
                if not forced_no_abstention:
                    continue
            elif context_method is not ContextMethodName.NO_OUTSIDE_CONTEXT:
                assigned = assign_context_cell(
                    row.histogram,
                    order_context.centroids,
                    config.context.kmeans.assignment_tie_tolerance,
                )
                if assigned != context_cell:
                    continue
            conditioned = _conditioned_member_ranks(
                config,
                fold_ranks,
                coalition,
                epoch_index,
                references,
            )
            if conditioned is None:
                continue
            tensor = tensor_representation(conditioned, basis_size)
            if purification_enabled:
                if calibration is None:
                    continue
                design_row = proper_subset_design_row(conditioned, basis_size)
                held_innovations.append(
                    projection_residual(
                        tensor,
                        calibration.complete_nuisance_coefficients,
                        design_row,
                    )
                )
            else:
                held_innovations.append(tensor)
    moments = moments_from_held_fold_innovations(tuple(held_innovations))
    if moments is None:
        return None
    means, deviations = moments
    standardized = tuple(
        center_and_scale_atom(
            innovation,
            means,
            deviations,
            config.projection.atom_scale_floor,
        )
        for innovation in held_innovations
    )
    norm_reference = operational_norm_reference_quantile(
        standardized,
        config.evidence.operational_norm_reference_quantile,
    )
    return means, deviations, norm_reference


def _fit_projection_cell(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    coalition: CoalitionMembers,
    context_cell: BinIndex,
    epochs: tuple[EpochIndexValue, ...],
    basis_size: BasisSize,
    purification_enabled: Boolean,
    forced_no_abstention: Boolean,
    ridge_candidates: tuple[RidgePenalty, ...],
    cross_fitted_statistics: tuple[tuple[FiniteFloat, ...], tuple[FiniteFloat, ...], FiniteFloat]
    | None,
) -> ProjectionCellFitRecord:
    references = _conditional_rank_references(ranks, coalition, context_cell, epochs)
    if len(epochs) < _minimum_support(config, coalition.order) and not forced_no_abstention:
        return ProjectionCellFitRecord(
            context_cell=context_cell,
            conditional_rank_references=references,
            selected_ridge_penalty=None,
            complete_nuisance_coefficients=(),
            coordinate_means=(),
            coordinate_deviations=(),
            operational_norm_reference=None,
            state=SupportState.NOT_TESTED,
        )
    rows = _conditioned_rows(config, ranks, coalition, epochs, references)
    design_rows, tensors = _design_and_tensors(rows, basis_size)
    complete_fit = None
    if purification_enabled:
        complete_fit = calibrate_innovations_on_nuisance_fit(
            design_rows,
            tensors,
            ridge_candidates,
            config.projection.cross_validation.fold_count,
            config.projection.selection_tie_tolerance_mse,
            config.projection.zero_ridge_svd_relative_cutoff,
            config.projection.atom_scale_floor,
        )
    if cross_fitted_statistics is None or (purification_enabled and complete_fit is None):
        return ProjectionCellFitRecord(
            context_cell=context_cell,
            conditional_rank_references=references,
            selected_ridge_penalty=None,
            complete_nuisance_coefficients=(),
            coordinate_means=(),
            coordinate_deviations=(),
            operational_norm_reference=None,
            state=SupportState.NOT_TESTED,
        )
    means, deviations, norm_reference = cross_fitted_statistics
    return ProjectionCellFitRecord(
        context_cell=context_cell,
        conditional_rank_references=references,
        selected_ridge_penalty=(
            None if complete_fit is None else complete_fit.selected_ridge_penalty
        ),
        complete_nuisance_coefficients=(
            () if complete_fit is None else complete_fit.complete_nuisance_coefficients
        ),
        coordinate_means=means,
        coordinate_deviations=deviations,
        operational_norm_reference=norm_reference,
        state=SupportState.SUPPORTED,
    )


def build_emhi_fit_artifact(
    config: ScientificConfig,
    scores: DetectorScoreArtifactRecord,
    ranks: MarginalRankArtifactRecord,
    split: DatasetSplitRecord,
    method_name: MethodName,
    context_method: ContextMethodName,
    maximum_order: CoalitionOrder,
    basis_size: BasisSize,
    cell_count: CellCount,
    purification_enabled: Boolean,
    forced_no_abstention: Boolean,
    dependency_fingerprint: MaterialDependencyFingerprint,
    ridge_candidates: tuple[RidgePenalty, ...] | None = None,
) -> EMHIFitArtifactRecord:
    if context_method is ContextMethodName.NO_OUTSIDE_CONTEXT:
        cell_count = NO_OUTSIDE_CONTEXT_CELL_COUNT
    if context_method is ContextMethodName.ORACLE_OUTSIDE_LATENT_CONTEXT:
        raise ValueError(f"{context_method.value} requires its specialized validation route")
    candidates = (
        config.projection.ridge_candidates if ridge_candidates is None else ridge_candidates
    )
    coalitions = enumerate_coalitions(split.selected_client_ids, maximum_order)
    order_contexts = tuple(
        _fit_order_context(
            config,
            ranks,
            coalitions,
            split.nuisance_fit_epochs,
            coalition_order,
            context_method,
            cell_count,
            None,
        )
        for coalition_order in CoalitionOrder
        if coalition_order <= maximum_order
    )
    coalition_fits: list[CoalitionFitRecord] = []
    fold_rank_cache: FoldRankCache = UserDict[
        tuple[RecordCount, RecordCount], MarginalRankArtifactRecord
    ]()
    order_context_cache: OrderContextCache = UserDict[
        tuple[RecordCount, RecordCount, CoalitionOrder], OrderContextFitRecord
    ]()
    for coalition in coalitions:
        order_context = next(
            context for context in order_contexts if context.coalition_order is coalition.order
        )
        if order_context.state is not SupportState.SUPPORTED:
            coalition_fits.append(
                CoalitionFitRecord(
                    coalition_client_ids=coalition.client_ids,
                    coalition_order=coalition.order,
                    cells=(),
                    state=SupportState.NOT_TESTED,
                )
            )
            continue
        cells: list[ProjectionCellFitRecord] = []
        for context_cell in range(len(order_context.centroids)):
            epochs = _coalition_cell_epochs(
                config,
                ranks,
                coalition,
                split.nuisance_fit_epochs,
                order_context.centroids,
                context_cell,
                context_method,
                None,
            )
            if len(epochs) < _minimum_support(config, coalition.order) and forced_no_abstention:
                epochs = split.nuisance_fit_epochs
            statistics = _cross_fitted_cell_statistics(
                config,
                scores,
                split,
                coalitions,
                coalition,
                context_cell,
                context_method,
                cell_count,
                basis_size,
                purification_enabled,
                forced_no_abstention,
                candidates,
                fold_rank_cache,
                order_context_cache,
            )
            cells.append(
                _fit_projection_cell(
                    config,
                    ranks,
                    coalition,
                    context_cell,
                    epochs,
                    basis_size,
                    purification_enabled,
                    forced_no_abstention,
                    candidates,
                    statistics,
                )
            )
        coalition_fits.append(
            CoalitionFitRecord(
                coalition_client_ids=coalition.client_ids,
                coalition_order=coalition.order,
                cells=tuple(cells),
                state=(
                    SupportState.SUPPORTED
                    if any(cell.state is SupportState.SUPPORTED for cell in cells)
                    else SupportState.NOT_TESTED
                ),
            )
        )
    return EMHIFitArtifactRecord(
        dataset_name=ranks.dataset_name,
        root_seed=ranks.root_seed,
        method_name=method_name,
        selected_client_ids=split.selected_client_ids,
        basis_size=basis_size,
        proper_subset_purification_enabled=purification_enabled,
        forced_no_abstention=forced_no_abstention,
        order_contexts=order_contexts,
        coalition_fits=tuple(coalition_fits),
        dependency_fingerprint=dependency_fingerprint,
    )
