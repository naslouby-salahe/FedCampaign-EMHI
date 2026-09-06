from math import log
from pathlib import Path
from time import perf_counter
from typing import cast

from fedcampaign_emhi.artifacts.provenance import (
    material_fingerprint,
    nuisance_context_boundary_digest,
)
from fedcampaign_emhi.artifacts.records import (
    BenignPartitionRecord,
    CampaignRecord,
    CampaignRegistryRecord,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
    EMHIFitArtifactRecord,
    MarginalRankArtifactRecord,
    PreparedDatasetRecord,
)
from fedcampaign_emhi.artifacts.storage import (
    build_artifact_layout,
    dataset_directory_stem,
    detector_score_artifact_id,
    detector_score_artifact_path,
    emhi_fit_artifact_id,
    emhi_fit_artifact_path,
    file_sha256,
    layer_artifact_id,
    marginal_rank_artifact_id,
    marginal_rank_artifact_path,
    method_artifact_stem,
    payload_digest,
    write_artifact_manifest,
    write_atomic_json,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.detection import (
    build_detector_score_artifact,
)
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    DatasetName,
    ExecutionRole,
    ExperimentName,
    MethodName,
    PartitionRole,
    PreprocessingLayer,
)
from fedcampaign_emhi.domain.types import (
    ArtifactIdentity,
    EpochIndexValue,
    FalseAlarmRate,
    OdiIndicator,
    RuntimeSeconds,
    SeedValue,
)
from fedcampaign_emhi.emhi.calibration import build_emhi_fit_artifact
from fedcampaign_emhi.emhi.structure import build_marginal_rank_artifact
from fedcampaign_emhi.evaluation.metrics import (
    decisive_order,
    earliest_local_stop,
    finite_horizon_pfa_point_estimate,
    mean_log_evidence_growth,
    order_evidence_share,
    paired_detection_indicator_difference,
    paired_stopping_time_difference,
    strict_odi_outcome,
    throughput,
)
from fedcampaign_emhi.evaluation.records import (
    OperationalCalibration,
    SequentialTrajectory,
)
from fedcampaign_emhi.evaluation.sequential import (
    TrajectoryCache,
    campaign_trajectory,
    global_stop_epoch,
    heldout_benign_false_stop_records,
    local_stop_epochs,
    operational_lead,
    statistical_lead,
    trajectory_context_coverage,
)
from fedcampaign_emhi.experiments.execution import (
    campaign_dataset,
    campaigns_logger,
    emhi_method_specification,
    experiment_contract,
)
from fedcampaign_emhi.experiments.technical_retry import with_technical_retry


def preprocessing_paths(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
) -> tuple[Path, Path, Path, Path, Path]:
    layout = build_artifact_layout(loaded, repository)
    root = layout.roots.outputs_root / "preprocessing"
    stem = dataset_directory_stem(dataset_name)
    return (
        root / "inventories" / f"{stem}.json",
        root / "prepared" / f"{stem}.json",
        root / "splits" / f"{stem}.json",
        root / "metadata" / f"{stem}-benign-partitions.json",
        root / "metadata" / f"{stem}-campaign-registry.json",
    )


def required_preprocessing_artifacts(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> tuple[Path, ...]:
    contract = experiment_contract(loaded.values, experiment_name)
    if not contract.uses_real_seeds:
        return ()
    return preprocessing_paths(loaded, repository, campaign_dataset(loaded, experiment_name))


def _materialize_detector_scores(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
) -> Path:
    _inventory_path, prepared_path, split_path, _partitions_path, _campaigns_path = (
        preprocessing_paths(loaded, repository, dataset_name)
    )
    detector_digest = payload_digest(
        cast(YamlNode, loaded.values.detectors.model_dump(mode="json"))
    )
    seed_digest = payload_digest(cast(YamlNode, {"root_seed": root_seed}))
    fingerprint = material_fingerprint(
        detector_digest,
        (file_sha256(prepared_path), file_sha256(split_path), seed_digest),
    )
    destination = detector_score_artifact_path(loaded, repository, dataset_name, root_seed)
    if destination.is_file():
        try:
            existing = DetectorScoreArtifactRecord.model_validate_json(destination.read_bytes())
        except ValueError:
            existing = None
        if existing is not None and existing.dependency_fingerprint == fingerprint:
            campaigns_logger().info(
                "reuse_decision artifact=detector_scores dataset=%s seed=%s decision=reused",
                dataset_name.value,
                root_seed,
            )
            return destination
    campaigns_logger().info(
        "reuse_decision artifact=detector_scores dataset=%s seed=%s decision=rebuilt",
        dataset_name.value,
        root_seed,
    )
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    record = build_detector_score_artifact(
        loaded.values,
        prepared,
        split,
        dataset_name,
        root_seed,
        fingerprint,
    )
    layout = build_artifact_layout(loaded, repository)
    content_hash = write_atomic_json(
        destination,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    write_artifact_manifest(
        loaded,
        repository,
        destination,
        detector_score_artifact_id(dataset_name, root_seed),
        content_hash,
        fingerprint,
        (
            layer_artifact_id(dataset_name, PreprocessingLayer.PREPARED),
            layer_artifact_id(dataset_name, PreprocessingLayer.SPLITS),
        ),
    )
    return destination


def _materialize_marginal_ranks(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
    score_path: Path,
) -> Path:
    _inventory_path, _prepared_path, split_path, _partitions_path, _campaigns_path = (
        preprocessing_paths(loaded, repository, dataset_name)
    )
    scores = DetectorScoreArtifactRecord.model_validate_json(score_path.read_bytes())
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    rank_digest = payload_digest(
        cast(YamlNode, {"rank_clip_epsilon": loaded.values.context.rank_clip_epsilon})
    )
    fingerprint = material_fingerprint(
        rank_digest,
        (file_sha256(score_path), file_sha256(split_path)),
    )
    destination = marginal_rank_artifact_path(loaded, repository, dataset_name, root_seed)
    if destination.is_file():
        try:
            existing = MarginalRankArtifactRecord.model_validate_json(destination.read_bytes())
        except ValueError:
            existing = None
        if existing is not None and existing.dependency_fingerprint == fingerprint:
            campaigns_logger().info(
                "reuse_decision artifact=marginal_ranks dataset=%s seed=%s decision=reused",
                dataset_name.value,
                root_seed,
            )
            return destination
    campaigns_logger().info(
        "reuse_decision artifact=marginal_ranks dataset=%s seed=%s decision=rebuilt",
        dataset_name.value,
        root_seed,
    )
    record = build_marginal_rank_artifact(
        scores,
        split.nuisance_fit_epochs,
        loaded.values.context.rank_clip_epsilon,
        fingerprint,
    )
    layout = build_artifact_layout(loaded, repository)
    content_hash = write_atomic_json(
        destination,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    write_artifact_manifest(
        loaded,
        repository,
        destination,
        marginal_rank_artifact_id(dataset_name, root_seed),
        content_hash,
        fingerprint,
        (
            detector_score_artifact_id(dataset_name, root_seed),
            layer_artifact_id(dataset_name, PreprocessingLayer.SPLITS),
        ),
    )
    return destination


def _materialize_emhi_fit(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
    method_name: MethodName,
    score_path: Path,
    rank_path: Path,
) -> Path:
    specification = emhi_method_specification(method_name)
    if specification is None:
        raise ValueError(f"method {method_name.value} is not an EMHI hierarchy")
    _inventory_path, _prepared_path, split_path, _partitions_path, _campaigns_path = (
        preprocessing_paths(loaded, repository, dataset_name)
    )
    method_digest = payload_digest(
        cast(
            YamlNode,
            {
                "method_name": method_name.value,
                "context_method": specification.context_method.value,
                "maximum_order": specification.maximum_order,
                "basis_size": loaded.values.basis.primary_size,
                "cell_count": loaded.values.context.primary_cell_count,
                "purification_enabled": specification.purification_enabled,
            },
        )
    )
    fingerprint = material_fingerprint(
        nuisance_context_boundary_digest(loaded.values),
        (
            method_digest,
            file_sha256(score_path),
            file_sha256(rank_path),
            file_sha256(split_path),
        ),
    )
    destination = emhi_fit_artifact_path(
        loaded,
        repository,
        dataset_name,
        root_seed,
        method_name,
    )
    if destination.is_file():
        try:
            existing = EMHIFitArtifactRecord.model_validate_json(destination.read_bytes())
        except ValueError:
            existing = None
        if existing is not None and existing.dependency_fingerprint == fingerprint:
            campaigns_logger().info(
                "reuse_decision artifact=emhi_fit dataset=%s seed=%s method=%s decision=reused",
                dataset_name.value,
                root_seed,
                method_name.value,
            )
            return destination
    campaigns_logger().info(
        "reuse_decision artifact=emhi_fit dataset=%s seed=%s method=%s decision=rebuilt",
        dataset_name.value,
        root_seed,
        method_name.value,
    )
    scores = DetectorScoreArtifactRecord.model_validate_json(score_path.read_bytes())
    ranks = MarginalRankArtifactRecord.model_validate_json(rank_path.read_bytes())
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    record = build_emhi_fit_artifact(
        loaded.values,
        scores,
        ranks,
        split,
        method_name,
        specification.context_method,
        specification.maximum_order,
        loaded.values.basis.primary_size,
        loaded.values.context.primary_cell_count,
        specification.purification_enabled,
        False,
        fingerprint,
    )
    layout = build_artifact_layout(loaded, repository)
    content_hash = write_atomic_json(
        destination,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    write_artifact_manifest(
        loaded,
        repository,
        destination,
        emhi_fit_artifact_id(dataset_name, root_seed, method_name),
        content_hash,
        fingerprint,
        (
            detector_score_artifact_id(dataset_name, root_seed),
            marginal_rank_artifact_id(dataset_name, root_seed),
            layer_artifact_id(dataset_name, PreprocessingLayer.SPLITS),
        ),
    )
    return destination


def local_pfa_target(
    loaded: LoadedScientificConfiguration,
    experiment_name: ExperimentName,
) -> FalseAlarmRate:
    if experiment_name is ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE:
        return loaded.values.local_policy.strong_horizon_pfa_target
    return loaded.values.local_policy.primary_horizon_pfa_target


def calibration_payload(calibration: OperationalCalibration) -> YamlNode:
    global_point = calibration.global_operating_point
    return {
        "global": {
            "threshold": global_point.threshold,
            "calibration_false_stop_counts": list(global_point.calibration_false_stop_counts),
            "calibration_horizon_count": global_point.calibration_horizon_count,
            "heldout_false_stop_count": global_point.heldout_false_stop_count,
            "heldout_horizon_count": global_point.heldout_horizon_count,
            "heldout_pfa_point_estimate": (
                None
                if global_point.heldout_horizon_count == 0
                else finite_horizon_pfa_point_estimate(
                    global_point.heldout_false_stop_count,
                    global_point.heldout_horizon_count,
                )
            ),
            "heldout_upper_pfa": global_point.heldout_upper_pfa,
        },
        "local": [
            {
                "client_id": point.client_id,
                "policy": None
                if point.policy is None
                else {
                    "threshold": point.policy.threshold,
                    "required_exceedances": point.policy.required_exceedances,
                    "window_epochs": point.policy.window_epochs,
                },
                "calibration_false_stop_count": point.calibration_false_stop_count,
                "heldout_false_stop_count": point.heldout_false_stop_count,
                "heldout_horizon_count": point.heldout_horizon_count,
                "heldout_upper_pfa": point.heldout_upper_pfa,
            }
            for point in calibration.local_operating_points
        ],
    }


def _trajectory_decisive_order(
    loaded: LoadedScientificConfiguration,
    trajectory: SequentialTrajectory,
    stop_epoch: EpochIndexValue | None,
) -> CoalitionOrder | None:
    if stop_epoch is None:
        return None
    row = next((item for item in trajectory.epochs if item.epoch_index == stop_epoch), None)
    if row is None:
        return None
    return decisive_order(
        row.order_factors,
        loaded.values.numerics.deterministic_comparison_tolerance,
    )


def build_campaign_rows(
    loaded: LoadedScientificConfiguration,
    scores: DetectorScoreArtifactRecord,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    campaigns: CampaignRegistryRecord,
    calibration: OperationalCalibration,
) -> tuple[tuple[YamlNode, ...], tuple[OdiIndicator, ...]]:
    rows: list[YamlNode] = []
    odi_values: list[OdiIndicator] = []
    for campaign in campaigns.campaigns:
        row, indicator = _campaign_row(loaded, scores, ranks, fit, calibration, campaign)
        rows.append(row)
        odi_values.append(indicator)
    return tuple(rows), tuple(odi_values)


def _campaign_row(
    loaded: LoadedScientificConfiguration,
    scores: DetectorScoreArtifactRecord,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    calibration: OperationalCalibration,
    campaign: CampaignRecord,
) -> tuple[YamlNode, OdiIndicator]:
    threshold = calibration.global_operating_point.threshold
    started = perf_counter()
    trajectory = campaign_trajectory(loaded.values, ranks, fit, campaign)
    elapsed: RuntimeSeconds = perf_counter() - started
    evaluation_epochs = tuple(row.epoch_index for row in trajectory.epochs)
    global_stop = None if threshold is None else global_stop_epoch(trajectory, threshold)
    local_stops = local_stop_epochs(
        scores,
        calibration.local_operating_points,
        evaluation_epochs,
    )
    odi = strict_odi_outcome(global_stop, local_stops)
    earliest_local = earliest_local_stop(local_stops)
    statistical = (
        None
        if global_stop is None or earliest_local is None
        else statistical_lead(earliest_local, global_stop)
    )
    operational = (
        None
        if global_stop is None or earliest_local is None
        else operational_lead(
            earliest_local,
            global_stop,
            elapsed,
            loaded.values.time.real_data_epoch_seconds,
        )
    )
    coverage = trajectory_context_coverage(trajectory)
    decisive = _trajectory_decisive_order(loaded, trajectory, global_stop)
    indicator: OdiIndicator = odi.indicator
    stop_row = next(
        (item for item in trajectory.epochs if item.epoch_index == global_stop),
        None,
    )
    order_share = None
    if stop_row is not None and decisive is not None:
        matching_factor = next(
            (factor for order, factor in stop_row.order_factors if order is decisive),
            None,
        )
        if matching_factor is not None:
            order_share = order_evidence_share(
                matching_factor,
                tuple(factor for _order, factor in stop_row.order_factors),
                loaded.values.numerics.metric_denominator_floor,
            )
    log_growth = (
        None
        if not trajectory.epochs
        else mean_log_evidence_growth(
            tuple(log(item.global_evidence_factor) for item in trajectory.epochs)
        )
    )
    scored_coalitions = 0 if stop_row is None else stop_row.scored_coalition_count
    return (
        {
            "start_epoch": campaign.start_epoch,
            "end_epoch": campaign.end_epoch,
            "participating_client_ids": list(campaign.participating_client_ids),
            "global_stop_epoch": global_stop,
            "local_stop_epochs": list(local_stops),
            "local_min_stop_epoch": earliest_local,
            "strict_odi": indicator,
            "statistical_lead_epochs": statistical,
            "operational_lead_epochs": operational,
            "global_detected_within_horizon": odi.global_detection_indicator,
            "local_detected_within_horizon": 0 if earliest_local is None else 1,
            "paired_stopping_time_difference": (
                None
                if global_stop is None or earliest_local is None
                else paired_stopping_time_difference(global_stop, earliest_local)
            ),
            "paired_detection_indicator_difference": paired_detection_indicator_difference(
                bool(odi.global_detection_indicator), earliest_local is not None
            ),
            "decisive_order": decisive,
            "order_evidence_share": order_share,
            "mean_log_evidence_growth": log_growth,
            "context_coverage": coverage,
            "abstention_rate": 1.0 - coverage,
            "server_latency_seconds": elapsed,
            "end_to_end_latency_seconds": elapsed,
            "throughput": None if elapsed <= 0.0 else throughput(scored_coalitions, elapsed),
        },
        indicator,
    )


def build_heldout_rows(
    loaded: LoadedScientificConfiguration,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    partitions: BenignPartitionRecord,
    calibration: OperationalCalibration,
    trajectory_cache: TrajectoryCache,
) -> tuple[YamlNode, ...]:
    threshold = calibration.global_operating_point.threshold
    if threshold is None:
        return ()
    records = heldout_benign_false_stop_records(
        loaded.values,
        ranks,
        fit,
        partitions,
        threshold,
        trajectory_cache=trajectory_cache,
    )
    return tuple(
        {
            "split_role": PartitionRole.HELDOUT_BENIGN.value,
            "horizon_index": index,
            "start_epoch": horizon.start_epoch,
            "threshold": threshold,
            "false_campaign": 0 if stop_epoch is None else 1,
            "first_stop_epoch": stop_epoch,
            "context_coverage": trajectory_context_coverage(trajectory),
            "abstention_rate": 1.0 - trajectory_context_coverage(trajectory),
            "global_evidence_factor": (
                1.0 if not trajectory.epochs else trajectory.epochs[-1].global_evidence_factor
            ),
        }
        for index, (horizon, trajectory, stop_epoch) in enumerate(records)
    )


def evaluation_artifact_id(
    experiment_name: ExperimentName,
    execution_role: ExecutionRole,
    method_name: MethodName,
    seed: SeedValue,
) -> ArtifactIdentity:
    return (
        f"evaluation.{experiment_name.value}.{execution_role.value}."
        f"{method_artifact_stem(method_name)}.seed-{seed}"
    )


def materialize_detector_scores_with_retry(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    seed: SeedValue,
) -> Path:
    return with_technical_retry(
        loaded,
        lambda: _materialize_detector_scores(loaded, repository, dataset_name, seed),
    )


def materialize_marginal_ranks_with_retry(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    seed: SeedValue,
    score_path: Path,
) -> Path:
    return with_technical_retry(
        loaded,
        lambda: _materialize_marginal_ranks(loaded, repository, dataset_name, seed, score_path),
    )


def materialize_emhi_fit_with_retry(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    seed: SeedValue,
    method_name: MethodName,
    score_path: Path,
    rank_path: Path,
) -> Path:
    return with_technical_retry(
        loaded,
        lambda: _materialize_emhi_fit(
            loaded, repository, dataset_name, seed, method_name, score_path, rank_path
        ),
    )
