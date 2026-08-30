from dataclasses import dataclass

from fedcampaign_emhi.artifacts.records import (
    CampaignRecord,
    CoalitionFitRecord,
    DetectorScoreArtifactRecord,
    EMHIFitArtifactRecord,
    MarginalRankArtifactRecord,
    OrderContextFitRecord,
    ProjectionCellFitRecord,
)
from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.detection.local_policy import first_local_stop_epoch, score_exceeds_threshold
from fedcampaign_emhi.domain.enums import ClaimState, CoalitionOrder, ContextMethodName
from fedcampaign_emhi.domain.types import (
    BinIndex,
    Boolean,
    ClientId,
    CoalitionMembers,
    EpochIndexValue,
    EpochSeconds,
    EvidenceFactor,
    FiniteFloat,
    PositiveEpochCount,
    Probability,
    RankReference,
    RankValue,
    ThresholdValue,
)
from fedcampaign_emhi.emhi.basis import tensor_representation
from fedcampaign_emhi.emhi.contexts import (
    assign_context_cell,
    exact_exclusion_members,
    inclusive_context_members,
    leave_one_out_context_members,
    outside_context_histogram,
    partial_coalition_context_members,
)
from fedcampaign_emhi.emhi.evidence import (
    across_order_aggregate,
    operational_evidence_factor,
    within_order_aggregate,
)
from fedcampaign_emhi.emhi.innovations import center_and_scale_atom, projection_residual
from fedcampaign_emhi.emhi.projection import proper_subset_design_row
from fedcampaign_emhi.emhi.ranks import coalition_conditioned_residual_rank, rank_at_epoch
from fedcampaign_emhi.emhi.sequential import (
    coalition_materially_active,
    first_global_stop_epoch,
    trailing_window_support_predicate,
)
from fedcampaign_emhi.evaluation.records import (
    ClientLocalOperatingPoint,
    CoalitionEpochEvidence,
    EpochOperationalEvidence,
    SequentialTrajectory,
)


@dataclass(frozen=True)
class CampaignReplayPlan:
    warmup_epochs: tuple[EpochIndexValue, ...]
    campaign_epochs: tuple[EpochIndexValue, ...]
    global_state_reset: Boolean
    local_persistence_reset: Boolean


def campaign_replay_plan(
    campaign_start_epoch: EpochIndexValue,
    prestart_warmup_epochs: PositiveEpochCount,
    evaluation_horizon_epochs: PositiveEpochCount,
) -> CampaignReplayPlan:
    if prestart_warmup_epochs <= 0 or evaluation_horizon_epochs <= 0:
        raise ValueError("warm-up and horizon must be positive")
    warmup = tuple(range(campaign_start_epoch - prestart_warmup_epochs, campaign_start_epoch))
    campaign = tuple(range(campaign_start_epoch, campaign_start_epoch + evaluation_horizon_epochs))
    return CampaignReplayPlan(
        warmup_epochs=warmup,
        campaign_epochs=campaign,
        global_state_reset=True,
        local_persistence_reset=True,
    )


def statistical_lead(
    earliest_local_stop_epoch: EpochIndexValue, global_stop_epoch: EpochIndexValue
) -> FiniteFloat:
    return earliest_local_stop_epoch - global_stop_epoch


def operational_lead(
    earliest_local_stop_epoch: EpochIndexValue,
    global_stop_epoch: EpochIndexValue,
    detection_delay_seconds: FiniteFloat,
    real_data_epoch_seconds: EpochSeconds,
) -> FiniteFloat:
    delay_in_epochs = detection_delay_seconds / real_data_epoch_seconds
    return earliest_local_stop_epoch - (global_stop_epoch + delay_in_epochs)


def score_at_epoch(
    scores: DetectorScoreArtifactRecord,
    client_id: ClientId,
    epoch_index: EpochIndexValue,
) -> FiniteFloat | None:
    stream = next(
        (stream for stream in scores.client_streams if stream.client_id == client_id),
        None,
    )
    if stream is None:
        return None
    return next(
        (
            score
            for epoch, score in zip(stream.epoch_indexes, stream.scores, strict=True)
            if epoch == epoch_index
        ),
        None,
    )


def scores_for_epochs(
    scores: DetectorScoreArtifactRecord,
    client_id: ClientId,
    epochs: tuple[EpochIndexValue, ...],
) -> tuple[FiniteFloat, ...]:
    resolved: list[FiniteFloat] = []
    for epoch in epochs:
        score = score_at_epoch(scores, client_id, epoch)
        if score is None:
            raise ValueError(f"missing detector score for {client_id} at epoch {epoch}")
        resolved.append(score)
    return tuple(resolved)


def _order_context(
    fit: EMHIFitArtifactRecord, coalition_order: CoalitionOrder
) -> OrderContextFitRecord | None:
    return next(
        (
            context
            for context in fit.order_contexts
            if context.coalition_order is coalition_order and context.state is ClaimState.SUPPORTED
        ),
        None,
    )


def _context_members(
    context_method: ContextMethodName,
    selected_client_ids: tuple[ClientId, ...],
    coalition_client_ids: tuple[ClientId, ...],
) -> tuple[ClientId, ...]:
    if context_method in {
        ContextMethodName.EXACT_COALITION_EXCLUSION,
        ContextMethodName.FORCED_NO_ABSTENTION,
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
    raise ValueError(f"context method {context_method.value} requires specialized replay")


def _coalition_context_cell(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    coalition: CoalitionMembers,
    order_context: OrderContextFitRecord,
    epoch_index: EpochIndexValue,
) -> BinIndex | None:
    context_method = order_context.context_method
    if context_method is ContextMethodName.NO_OUTSIDE_CONTEXT:
        return 0
    lagged_epoch = epoch_index - config.context.outside_lag_epochs
    members = _context_members(context_method, ranks.selected_client_ids, coalition.client_ids)
    lagged_ranks = tuple(
        (client_id, rank)
        for client_id in members
        for rank in (rank_at_epoch(ranks, client_id, lagged_epoch),)
        if rank is not None
    )
    available = tuple(client_id for client_id, _rank in lagged_ranks)
    histogram = outside_context_histogram(
        lagged_ranks,
        available,
        members,
        config.context.outside_histogram_bin_count,
        config.context.minimum_available_outside_clients,
        config.context.minimum_available_outside_fraction,
    )
    if histogram.abstained or not order_context.centroids:
        if fit.forced_no_abstention and order_context.centroids:
            return 0
        return None
    return assign_context_cell(
        histogram.bin_mass,
        order_context.centroids,
        config.context.kmeans.assignment_tie_tolerance,
    )


def _projection_cell(
    coalition_fit: CoalitionFitRecord, context_cell: BinIndex
) -> ProjectionCellFitRecord | None:
    return next(
        (
            cell
            for cell in coalition_fit.cells
            if cell.context_cell == context_cell and cell.state is ClaimState.SUPPORTED
        ),
        None,
    )


def _conditioned_member_ranks(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    coalition_fit: CoalitionFitRecord,
    cell: ProjectionCellFitRecord,
    epoch_index: EpochIndexValue,
) -> tuple[RankValue, ...] | None:
    conditioned: list[RankValue] = []
    for client_id in coalition_fit.coalition_client_ids:
        marginal = rank_at_epoch(ranks, client_id, epoch_index)
        reference = next(
            (
                item
                for item in cell.conditional_rank_references
                if item.client_id == client_id and item.reference_ranks
            ),
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


def _coalition_standardized_atom_and_norm_at_epoch(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    coalition_fit: CoalitionFitRecord,
    epoch_index: EpochIndexValue,
) -> tuple[tuple[FiniteFloat, ...], FiniteFloat] | None:
    if coalition_fit.state is not ClaimState.SUPPORTED:
        return None
    order_context = _order_context(fit, coalition_fit.coalition_order)
    if order_context is None:
        return None
    coalition = CoalitionMembers(
        client_ids=coalition_fit.coalition_client_ids,
        order=coalition_fit.coalition_order,
    )
    context_cell = _coalition_context_cell(
        config,
        ranks,
        fit,
        coalition,
        order_context,
        epoch_index,
    )
    if context_cell is None:
        return None
    cell = _projection_cell(coalition_fit, context_cell)
    if (
        cell is None
        or cell.operational_norm_reference is None
        or not cell.coordinate_means
        or not cell.coordinate_deviations
    ):
        return None
    conditioned = _conditioned_member_ranks(config, ranks, coalition_fit, cell, epoch_index)
    if conditioned is None:
        return None
    tensor = tensor_representation(conditioned, fit.basis_size)
    if fit.proper_subset_purification_enabled:
        if not cell.complete_nuisance_coefficients:
            return None
        design_row = proper_subset_design_row(conditioned, fit.basis_size)
        raw_atom = projection_residual(tensor, cell.complete_nuisance_coefficients, design_row)
    else:
        raw_atom = tensor
    return (
        center_and_scale_atom(
            raw_atom,
            cell.coordinate_means,
            cell.coordinate_deviations,
            config.projection.atom_scale_floor,
        ),
        cell.operational_norm_reference,
    )


def coalition_standardized_atom_at_epoch(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    coalition_fit: CoalitionFitRecord,
    epoch_index: EpochIndexValue,
) -> tuple[FiniteFloat, ...] | None:
    resolved = _coalition_standardized_atom_and_norm_at_epoch(
        config, ranks, fit, coalition_fit, epoch_index
    )
    return None if resolved is None else resolved[0]


def coalition_evidence_at_epoch(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    coalition_fit: CoalitionFitRecord,
    epoch_index: EpochIndexValue,
) -> EvidenceFactor | None:
    resolved = _coalition_standardized_atom_and_norm_at_epoch(
        config, ranks, fit, coalition_fit, epoch_index
    )
    if resolved is None:
        return None
    standardized, norm_reference = resolved
    return operational_evidence_factor(
        standardized,
        norm_reference,
        config.projection.norm_reference_floor,
        config.evidence.clip_bound,
        config.evidence.bet_lambda,
    )


def operational_evidence_at_epoch(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    epoch_index: EpochIndexValue,
    maximum_order: CoalitionOrder | None = None,
) -> EpochOperationalEvidence:
    enabled_maximum = maximum_order or max(
        (context.coalition_order for context in fit.order_contexts),
        default=CoalitionOrder.ONE,
    )
    coalition_factors: list[CoalitionEpochEvidence] = []
    active_clients: set[ClientId] = set()
    eligible = 0
    for coalition_fit in fit.coalition_fits:
        if coalition_fit.coalition_order > enabled_maximum:
            continue
        eligible += 1
        factor = coalition_evidence_at_epoch(config, ranks, fit, coalition_fit, epoch_index)
        if factor is None:
            continue
        coalition_factors.append(
            CoalitionEpochEvidence(
                coalition_client_ids=coalition_fit.coalition_client_ids,
                coalition_order=coalition_fit.coalition_order,
                evidence_factor=factor,
            )
        )
        if coalition_materially_active(
            factor,
            config.distributed_support.material_coalition_evidence_threshold,
        ):
            active_clients.update(coalition_fit.coalition_client_ids)
    order_factors = tuple(
        (
            order,
            within_order_aggregate(
                tuple(
                    record.evidence_factor
                    for record in coalition_factors
                    if record.coalition_order is order
                )
            ),
        )
        for order in CoalitionOrder
        if order <= enabled_maximum
    )
    global_factor = across_order_aggregate(tuple(factor for _order, factor in order_factors))
    return EpochOperationalEvidence(
        epoch_index=epoch_index,
        global_evidence_factor=global_factor,
        order_factors=order_factors,
        coalition_factors=tuple(coalition_factors),
        materially_active_client_ids=tuple(sorted(active_clients)),
        scored_coalition_count=len(coalition_factors),
        eligible_coalition_count=eligible,
    )


def sequential_trajectory(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    epoch_indexes: tuple[EpochIndexValue, ...],
    maximum_order: CoalitionOrder | None = None,
) -> SequentialTrajectory:
    records = tuple(
        operational_evidence_at_epoch(config, ranks, fit, epoch_index, maximum_order)
        for epoch_index in epoch_indexes
    )
    active_history: list[tuple[ClientId, ...]] = []
    support: list[bool] = []
    for record in records:
        active_history.append(record.materially_active_client_ids)
        support.append(
            trailing_window_support_predicate(
                tuple(active_history),
                config.distributed_support.trailing_window_epochs,
                config.distributed_support.minimum_clients,
            )
        )
    return SequentialTrajectory(epochs=records, support_predicates=tuple(support))


def global_stop_epoch(
    trajectory: SequentialTrajectory, threshold: ThresholdValue
) -> EpochIndexValue | None:
    position = first_global_stop_epoch(
        tuple(record.global_evidence_factor for record in trajectory.epochs),
        trajectory.support_predicates,
        threshold,
    )
    if position is None:
        return None
    return trajectory.epochs[position].epoch_index


def local_stop_epochs(
    scores: DetectorScoreArtifactRecord,
    operating_points: tuple[ClientLocalOperatingPoint, ...],
    epoch_indexes: tuple[EpochIndexValue, ...],
) -> tuple[EpochIndexValue | None, ...]:
    stops: list[EpochIndexValue | None] = []
    for operating_point in operating_points:
        policy = operating_point.policy
        if policy is None:
            stops.append(None)
            continue
        exceedances = tuple(
            score_exceeds_threshold(score, policy.threshold)
            for score in scores_for_epochs(scores, operating_point.client_id, epoch_indexes)
        )
        position = first_local_stop_epoch(
            exceedances,
            policy.required_exceedances,
            policy.window_epochs,
        )
        stops.append(None if position is None else epoch_indexes[position])
    return tuple(stops)


def trajectory_context_coverage(trajectory: SequentialTrajectory) -> Probability:
    eligible = sum(record.eligible_coalition_count for record in trajectory.epochs)
    if eligible == 0:
        return 0.0
    scored = sum(record.scored_coalition_count for record in trajectory.epochs)
    return scored / eligible


def campaign_trajectory(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    campaign: CampaignRecord,
    maximum_order: CoalitionOrder | None = None,
) -> SequentialTrajectory:
    plan = campaign_replay_plan(
        campaign.start_epoch,
        config.campaign.prestart_warmup_epochs,
        config.campaign.evaluation_horizon_epochs,
    )
    return sequential_trajectory(config, ranks, fit, plan.campaign_epochs, maximum_order)
