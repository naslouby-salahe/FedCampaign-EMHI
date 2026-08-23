from dataclasses import dataclass

from fedcampaign_emhi.artifacts.records import (
    BenignHorizonRecord,
    BenignPartitionRecord,
    CampaignRecord,
    CoalitionFitRecord,
    DetectorScoreArtifactRecord,
    EMHIFitArtifactRecord,
    MarginalRankArtifactRecord,
    OrderContextFitRecord,
    ProjectionCellFitRecord,
)
from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.detection.local_policy import (
    candidate_thresholds_from_nuisance_scores,
    first_local_stop_epoch,
    heldout_false_stop_count,
    score_exceeds_threshold,
    select_immutable_local_policy,
)
from fedcampaign_emhi.domain.enums import ClaimState, CoalitionOrder
from fedcampaign_emhi.domain.types import (
    BinIndex,
    ClientId,
    CoalitionMembers,
    EpochIndexValue,
    EvidenceFactor,
    FalseAlarmRate,
    FiniteFloat,
    LocalPolicyArtifact,
    Probability,
    RankReference,
    RankValue,
    RecordCount,
    ThresholdValue,
)
from fedcampaign_emhi.emhi.basis import tensor_representation
from fedcampaign_emhi.emhi.contexts import (
    assign_context_cell,
    exact_exclusion_members,
    outside_context_histogram,
)
from fedcampaign_emhi.emhi.evidence import (
    across_order_aggregate,
    operational_evidence_factor,
    within_order_aggregate,
)
from fedcampaign_emhi.emhi.innovations import center_and_scale_atom, projection_residual
from fedcampaign_emhi.emhi.projection import proper_subset_design_row
from fedcampaign_emhi.emhi.ranks import coalition_conditioned_residual_rank
from fedcampaign_emhi.emhi.sequential import (
    coalition_materially_active,
    first_global_stop_epoch,
    trailing_window_support_predicate,
)
from fedcampaign_emhi.emhi.thresholds import (
    clopper_pearson_one_sided_upper_bound,
    select_calibrated_threshold,
)


@dataclass(frozen=True)
class CoalitionEpochEvidence:
    coalition_client_ids: tuple[ClientId, ...]
    coalition_order: CoalitionOrder
    evidence_factor: EvidenceFactor


@dataclass(frozen=True)
class EpochOperationalEvidence:
    epoch_index: EpochIndexValue
    global_evidence_factor: EvidenceFactor
    order_factors: tuple[tuple[CoalitionOrder, EvidenceFactor], ...]
    coalition_factors: tuple[CoalitionEpochEvidence, ...]
    materially_active_client_ids: tuple[ClientId, ...]
    scored_coalition_count: RecordCount
    eligible_coalition_count: RecordCount


@dataclass(frozen=True)
class SequentialTrajectory:
    epochs: tuple[EpochOperationalEvidence, ...]
    support_predicates: tuple[bool, ...]


@dataclass(frozen=True)
class CalibratedGlobalOperatingPoint:
    threshold: ThresholdValue | None
    calibration_false_stop_counts: tuple[RecordCount, ...]
    calibration_horizon_count: RecordCount
    heldout_false_stop_count: RecordCount
    heldout_horizon_count: RecordCount
    heldout_upper_pfa: Probability | None


@dataclass(frozen=True)
class ClientLocalOperatingPoint:
    client_id: ClientId
    policy: LocalPolicyArtifact | None
    calibration_false_stop_count: RecordCount | None
    heldout_false_stop_count: RecordCount | None
    heldout_horizon_count: RecordCount
    heldout_upper_pfa: Probability | None


@dataclass(frozen=True)
class OperationalCalibration:
    global_operating_point: CalibratedGlobalOperatingPoint
    local_operating_points: tuple[ClientLocalOperatingPoint, ...]


def _rank_at_epoch(
    ranks: MarginalRankArtifactRecord,
    client_id: ClientId,
    epoch_index: EpochIndexValue,
) -> RankValue | None:
    stream = next(
        (stream for stream in ranks.client_streams if stream.client_id == client_id),
        None,
    )
    if stream is None:
        return None
    return next(
        (
            rank
            for epoch, rank in zip(stream.epoch_indexes, stream.ranks, strict=True)
            if epoch == epoch_index
        ),
        None,
    )


def _score_at_epoch(
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


def _order_context(
    fit: EMHIFitArtifactRecord, coalition_order: CoalitionOrder
) -> OrderContextFitRecord | None:
    return next(
        (
            context
            for context in fit.order_contexts
            if context.coalition_order is coalition_order
            and context.state is ClaimState.SUPPORTED
        ),
        None,
    )


def _coalition_context_cell(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    coalition: CoalitionMembers,
    order_context: OrderContextFitRecord,
    epoch_index: EpochIndexValue,
) -> BinIndex | None:
    lagged_epoch = epoch_index - config.context.outside_lag_epochs
    complement = exact_exclusion_members(ranks.selected_client_ids, coalition.client_ids)
    lagged_ranks: list[tuple[ClientId, RankValue]] = []
    available: list[ClientId] = []
    for client_id in complement:
        rank = _rank_at_epoch(ranks, client_id, lagged_epoch)
        if rank is None:
            continue
        lagged_ranks.append((client_id, rank))
        available.append(client_id)
    histogram = outside_context_histogram(
        tuple(lagged_ranks),
        tuple(available),
        complement,
        config.context.outside_histogram_bin_count,
        config.context.minimum_available_outside_clients,
        config.context.minimum_available_outside_fraction,
    )
    if histogram.abstained or not order_context.centroids:
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
        marginal = _rank_at_epoch(ranks, client_id, epoch_index)
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


def coalition_evidence_at_epoch(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    coalition_fit: CoalitionFitRecord,
    epoch_index: EpochIndexValue,
) -> EvidenceFactor | None:
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
        or not cell.complete_nuisance_coefficients
        or not cell.coordinate_means
        or not cell.coordinate_deviations
    ):
        return None
    conditioned = _conditioned_member_ranks(
        config,
        ranks,
        coalition_fit,
        cell,
        epoch_index,
    )
    if conditioned is None:
        return None
    design_row = proper_subset_design_row(conditioned, config.basis.primary_size)
    tensor = tensor_representation(conditioned, config.basis.primary_size)
    raw_atom = projection_residual(
        tensor,
        cell.complete_nuisance_coefficients,
        design_row,
    )
    standardized = center_and_scale_atom(
        raw_atom,
        cell.coordinate_means,
        cell.coordinate_deviations,
        config.projection.atom_scale_floor,
    )
    return operational_evidence_factor(
        standardized,
        cell.operational_norm_reference,
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
    enabled_maximum = maximum_order or CoalitionOrder(int(config.study.maximum_coalition_order))
    coalition_factors: list[CoalitionEpochEvidence] = []
    active_clients: set[ClientId] = set()
    eligible = 0
    for coalition_fit in fit.coalition_fits:
        if coalition_fit.coalition_order > enabled_maximum:
            continue
        eligible += 1
        factor = coalition_evidence_at_epoch(
            config,
            ranks,
            fit,
            coalition_fit,
            epoch_index,
        )
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


def _trajectory_stop_position(
    trajectory: SequentialTrajectory, threshold: ThresholdValue
) -> EpochIndexValue | None:
    return first_global_stop_epoch(
        tuple(record.global_evidence_factor for record in trajectory.epochs),
        trajectory.support_predicates,
        threshold,
    )


def global_stop_epoch(
    trajectory: SequentialTrajectory, threshold: ThresholdValue
) -> EpochIndexValue | None:
    position = _trajectory_stop_position(trajectory, threshold)
    if position is None:
        return None
    return trajectory.epochs[position].epoch_index


def _horizon_trajectory(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    horizon: BenignHorizonRecord,
    maximum_order: CoalitionOrder | None = None,
) -> SequentialTrajectory:
    return sequential_trajectory(config, ranks, fit, horizon.epoch_indexes, maximum_order)


def calibrate_global_operating_point(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    partitions: BenignPartitionRecord,
    maximum_order: CoalitionOrder | None = None,
) -> CalibratedGlobalOperatingPoint:
    candidates = config.evidence.calibrated_finite_horizon.threshold_candidates
    calibration_trajectories = tuple(
        _horizon_trajectory(config, ranks, fit, horizon, maximum_order)
        for horizon in partitions.calibration_horizons
    )
    calibration_counts = tuple(
        sum(
            1
            for trajectory in calibration_trajectories
            if _trajectory_stop_position(trajectory, threshold) is not None
        )
        for threshold in candidates
    )
    selected = select_calibrated_threshold(
        candidates,
        calibration_counts,
        len(calibration_trajectories),
        config.evidence.calibrated_finite_horizon.calibration_confidence,
        config.evidence.calibrated_finite_horizon.target_pfa,
    )
    heldout_trajectories = tuple(
        _horizon_trajectory(config, ranks, fit, horizon, maximum_order)
        for horizon in partitions.heldout_horizons
    )
    heldout_false_stops = (
        0
        if selected is None
        else sum(
            1
            for trajectory in heldout_trajectories
            if _trajectory_stop_position(trajectory, selected) is not None
        )
    )
    heldout_upper = (
        None
        if selected is None or not heldout_trajectories
        else clopper_pearson_one_sided_upper_bound(
            heldout_false_stops,
            len(heldout_trajectories),
            config.evidence.calibrated_finite_horizon.calibration_confidence,
        )
    )
    return CalibratedGlobalOperatingPoint(
        threshold=selected,
        calibration_false_stop_counts=calibration_counts,
        calibration_horizon_count=len(calibration_trajectories),
        heldout_false_stop_count=heldout_false_stops,
        heldout_horizon_count=len(heldout_trajectories),
        heldout_upper_pfa=heldout_upper,
    )


def _scores_for_epochs(
    scores: DetectorScoreArtifactRecord,
    client_id: ClientId,
    epochs: tuple[EpochIndexValue, ...],
) -> tuple[FiniteFloat, ...]:
    resolved: list[FiniteFloat] = []
    for epoch in epochs:
        score = _score_at_epoch(scores, client_id, epoch)
        if score is None:
            raise ValueError(f"missing detector score for {client_id} at epoch {epoch}")
        resolved.append(score)
    return tuple(resolved)


def _horizon_exceedances(
    scores: DetectorScoreArtifactRecord,
    client_id: ClientId,
    horizon: BenignHorizonRecord,
    threshold: ThresholdValue,
) -> tuple[bool, ...]:
    return tuple(
        score_exceeds_threshold(score, threshold)
        for score in _scores_for_epochs(scores, client_id, horizon.epoch_indexes)
    )


def calibrate_client_local_operating_point(
    config: ScientificConfig,
    scores: DetectorScoreArtifactRecord,
    client_id: ClientId,
    nuisance_epochs: tuple[EpochIndexValue, ...],
    partitions: BenignPartitionRecord,
    target_pfa: FalseAlarmRate,
) -> ClientLocalOperatingPoint:
    nuisance_scores = _scores_for_epochs(scores, client_id, nuisance_epochs)
    thresholds = candidate_thresholds_from_nuisance_scores(
        nuisance_scores,
        config.local_policy.candidate_score_quantiles,
    )
    candidates = tuple(
        LocalPolicyArtifact(
            threshold=threshold,
            required_exceedances=persistence.required_exceedances,
            window_epochs=persistence.window_epochs,
        )
        for threshold in thresholds
        for persistence in config.local_policy.candidate_persistence
    )
    calibration_counts = tuple(
        heldout_false_stop_count(
            tuple(
                _horizon_exceedances(scores, client_id, horizon, candidate.threshold)
                for horizon in partitions.calibration_horizons
            ),
            candidate.required_exceedances,
            candidate.window_epochs,
        )
        for candidate in candidates
    )
    policy = select_immutable_local_policy(
        candidates,
        calibration_counts,
        len(partitions.calibration_horizons),
        config.local_policy.pfa_confidence,
        target_pfa,
    )
    if policy is None:
        return ClientLocalOperatingPoint(
            client_id=client_id,
            policy=None,
            calibration_false_stop_count=None,
            heldout_false_stop_count=None,
            heldout_horizon_count=len(partitions.heldout_horizons),
            heldout_upper_pfa=None,
        )
    selected_index = candidates.index(policy)
    heldout_count = heldout_false_stop_count(
        tuple(
            _horizon_exceedances(scores, client_id, horizon, policy.threshold)
            for horizon in partitions.heldout_horizons
        ),
        policy.required_exceedances,
        policy.window_epochs,
    )
    heldout_upper = (
        None
        if not partitions.heldout_horizons
        else clopper_pearson_one_sided_upper_bound(
            heldout_count,
            len(partitions.heldout_horizons),
            config.local_policy.pfa_confidence,
        )
    )
    return ClientLocalOperatingPoint(
        client_id=client_id,
        policy=policy,
        calibration_false_stop_count=calibration_counts[selected_index],
        heldout_false_stop_count=heldout_count,
        heldout_horizon_count=len(partitions.heldout_horizons),
        heldout_upper_pfa=heldout_upper,
    )


def calibrate_operating_points(
    config: ScientificConfig,
    scores: DetectorScoreArtifactRecord,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    nuisance_epochs: tuple[EpochIndexValue, ...],
    partitions: BenignPartitionRecord,
    target_pfa: FalseAlarmRate,
    maximum_order: CoalitionOrder | None = None,
) -> OperationalCalibration:
    return OperationalCalibration(
        global_operating_point=calibrate_global_operating_point(
            config,
            ranks,
            fit,
            partitions,
            maximum_order,
        ),
        local_operating_points=tuple(
            calibrate_client_local_operating_point(
                config,
                scores,
                client_id,
                nuisance_epochs,
                partitions,
                target_pfa,
            )
            for client_id in scores.selected_client_ids
        ),
    )


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
            for score in _scores_for_epochs(scores, operating_point.client_id, epoch_indexes)
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


def heldout_benign_false_stop_records(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    partitions: BenignPartitionRecord,
    threshold: ThresholdValue,
    maximum_order: CoalitionOrder | None = None,
) -> tuple[tuple[BenignHorizonRecord, SequentialTrajectory, EpochIndexValue | None], ...]:
    return tuple(
        (
            horizon,
            trajectory,
            global_stop_epoch(trajectory, threshold),
        )
        for horizon in partitions.heldout_horizons
        for trajectory in (_horizon_trajectory(config, ranks, fit, horizon, maximum_order),)
    )


def campaign_trajectory(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    campaign: CampaignRecord,
    maximum_order: CoalitionOrder | None = None,
) -> SequentialTrajectory:
    epoch_indexes = tuple(
        range(
            campaign.start_epoch,
            campaign.start_epoch + config.campaign.evaluation_horizon_epochs,
        )
    )
    return sequential_trajectory(config, ranks, fit, epoch_indexes, maximum_order)
