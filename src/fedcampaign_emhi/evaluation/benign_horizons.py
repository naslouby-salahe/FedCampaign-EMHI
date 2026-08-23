from fedcampaign_emhi.artifacts.records import (
    BenignHorizonRecord,
    BenignPartitionRecord,
    DetectorScoreArtifactRecord,
    EMHIFitArtifactRecord,
    MarginalRankArtifactRecord,
)
from fedcampaign_emhi.config.schema import ScientificConfig
from fedcampaign_emhi.detection.local_policy import (
    candidate_thresholds_from_nuisance_scores,
    heldout_false_stop_count,
    score_exceeds_threshold,
    select_immutable_local_policy,
)
from fedcampaign_emhi.domain.enums import CoalitionOrder
from fedcampaign_emhi.domain.types import (
    BenignHorizon,
    ClientId,
    EpochIndexValue,
    FalseAlarmRate,
    LocalPolicyArtifact,
    ThresholdValue,
)
from fedcampaign_emhi.emhi.thresholds import (
    clopper_pearson_one_sided_upper_bound,
    select_calibrated_threshold,
)
from fedcampaign_emhi.evaluation.campaign_replay import (
    global_stop_epoch,
    scores_for_epochs,
    sequential_trajectory,
)
from fedcampaign_emhi.evaluation.records import (
    CalibratedGlobalOperatingPoint,
    ClientLocalOperatingPoint,
    OperationalCalibration,
    SequentialTrajectory,
)


def sequential_stop_reset_epochs(
    horizons: tuple[BenignHorizon, ...],
) -> tuple[EpochIndexValue, ...]:
    return tuple(horizon.start_epoch for horizon in horizons)


def horizons_are_nonoverlapping(horizons: tuple[BenignHorizon, ...]) -> bool:
    seen: list[EpochIndexValue] = []
    for horizon in horizons:
        for epoch in horizon.epoch_indexes:
            if epoch in seen:
                return False
            seen.append(epoch)
    return True


def horizon_trajectory(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    horizon: BenignHorizonRecord,
    maximum_order: CoalitionOrder | None = None,
) -> SequentialTrajectory:
    return sequential_trajectory(config, ranks, fit, horizon.epoch_indexes, maximum_order)


def _trajectory_stops(
    trajectory: SequentialTrajectory,
    threshold: ThresholdValue,
) -> bool:
    return global_stop_epoch(trajectory, threshold) is not None


def calibrate_global_operating_point(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    partitions: BenignPartitionRecord,
    maximum_order: CoalitionOrder | None = None,
) -> CalibratedGlobalOperatingPoint:
    calibration_horizons = partitions.calibration_horizons
    heldout_horizons = partitions.heldout_horizons
    if not calibration_horizons:
        return CalibratedGlobalOperatingPoint(
            threshold=None,
            calibration_false_stop_counts=(),
            calibration_horizon_count=0,
            heldout_false_stop_count=0,
            heldout_horizon_count=len(heldout_horizons),
            heldout_upper_pfa=None,
        )
    candidates = config.evidence.calibrated_finite_horizon.threshold_candidates
    calibration_trajectories = tuple(
        horizon_trajectory(config, ranks, fit, horizon, maximum_order)
        for horizon in calibration_horizons
    )
    calibration_counts = tuple(
        sum(1 for trajectory in calibration_trajectories if _trajectory_stops(trajectory, threshold))
        for threshold in candidates
    )
    selected = select_calibrated_threshold(
        candidates,
        calibration_counts,
        len(calibration_trajectories),
        config.evidence.calibrated_finite_horizon.calibration_confidence,
        config.evidence.calibrated_finite_horizon.target_pfa,
    )
    if selected is None:
        return CalibratedGlobalOperatingPoint(
            threshold=None,
            calibration_false_stop_counts=calibration_counts,
            calibration_horizon_count=len(calibration_trajectories),
            heldout_false_stop_count=0,
            heldout_horizon_count=len(heldout_horizons),
            heldout_upper_pfa=None,
        )
    heldout_trajectories = tuple(
        horizon_trajectory(config, ranks, fit, horizon, maximum_order)
        for horizon in heldout_horizons
    )
    heldout_false_stops = sum(
        1 for trajectory in heldout_trajectories if _trajectory_stops(trajectory, selected)
    )
    heldout_upper = (
        None
        if not heldout_trajectories
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


def _horizon_exceedances(
    scores: DetectorScoreArtifactRecord,
    client_id: ClientId,
    horizon: BenignHorizonRecord,
    threshold: ThresholdValue,
) -> tuple[bool, ...]:
    return tuple(
        score_exceeds_threshold(score, threshold)
        for score in scores_for_epochs(scores, client_id, horizon.epoch_indexes)
    )


def calibrate_client_local_operating_point(
    config: ScientificConfig,
    scores: DetectorScoreArtifactRecord,
    client_id: ClientId,
    nuisance_epochs: tuple[EpochIndexValue, ...],
    partitions: BenignPartitionRecord,
    target_pfa: FalseAlarmRate,
) -> ClientLocalOperatingPoint:
    if not partitions.calibration_horizons:
        return ClientLocalOperatingPoint(
            client_id=client_id,
            policy=None,
            calibration_false_stop_count=None,
            heldout_false_stop_count=None,
            heldout_horizon_count=len(partitions.heldout_horizons),
            heldout_upper_pfa=None,
        )
    nuisance_scores = scores_for_epochs(scores, client_id, nuisance_epochs)
    if not nuisance_scores:
        return ClientLocalOperatingPoint(
            client_id=client_id,
            policy=None,
            calibration_false_stop_count=None,
            heldout_false_stop_count=None,
            heldout_horizon_count=len(partitions.heldout_horizons),
            heldout_upper_pfa=None,
        )
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
        for trajectory in (horizon_trajectory(config, ranks, fit, horizon, maximum_order),)
    )
