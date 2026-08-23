from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import cast

from fedcampaign_emhi.analysis.summaries import build_seed_summary
from fedcampaign_emhi.artifacts.paths import build_artifact_layout
from fedcampaign_emhi.artifacts.provenance import material_fingerprint
from fedcampaign_emhi.artifacts.records import (
    BenignPartitionRecord,
    CampaignRegistryRecord,
    CompletionRecord,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
    EMHIFitArtifactRecord,
    MarginalRankArtifactRecord,
    ScientificCellRecord,
    SeedSummaryRecord,
)
from fedcampaign_emhi.artifacts.storage import file_sha256, payload_digest, write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ExecutionRole,
    ExperimentName,
    ExperimentState,
    MethodName,
    PartitionRole,
    PreprocessingLayer,
)
from fedcampaign_emhi.domain.types import (
    ArtifactIdentity,
    EpochIndexValue,
    FalseAlarmRate,
    FiniteFloat,
    MaterialDependencyFingerprint,
    OdiIndicator,
    RelativePath,
    RuntimeSeconds,
    SeedValue,
)
from fedcampaign_emhi.evaluation.campaign_replay import operational_lead, statistical_lead
from fedcampaign_emhi.evaluation.metrics import decisive_order, earliest_local_stop
from fedcampaign_emhi.evaluation.operational import (
    OperationalCalibration,
    SequentialTrajectory,
    calibrate_operating_points,
    campaign_trajectory,
    global_stop_epoch,
    heldout_benign_false_stop_records,
    local_stop_epochs,
    trajectory_context_coverage,
)
from fedcampaign_emhi.evaluation.records import odi_evaluation_record
from fedcampaign_emhi.execution.preprocess import dataset_directory_stem, layer_artifact_id


@dataclass(frozen=True)
class RealMethodSeedExecution:
    raw_evaluation_path: Path
    cell_path: Path
    seed_summary_path: Path
    seed_summary: SeedSummaryRecord
    state: ExperimentState


def maximum_order_for_method(method_name: MethodName) -> CoalitionOrder | None:
    if method_name is MethodName.EXCLUSION_MATCHED_ORDER_ONE_EMHI:
        return CoalitionOrder.ONE
    if method_name is MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI:
        return CoalitionOrder.TWO
    if method_name is MethodName.FULL_FEDCAMPAIGN_EMHI:
        return None
    raise ValueError(f"method {method_name.value} is not an exclusion-matched EMHI order restriction")


def _method_slug(method_name: MethodName) -> RelativePath:
    return method_name.value.lower().replace(" ", "-").replace("≤", "at-most-").replace("_", "-")


def _score_artifact_id(dataset_stem: RelativePath, seed: SeedValue) -> ArtifactIdentity:
    return f"detector-scores.{dataset_stem}.seed-{seed}"


def _rank_artifact_id(dataset_stem: RelativePath, seed: SeedValue) -> ArtifactIdentity:
    return f"marginal-ranks.{dataset_stem}.seed-{seed}"


def _fit_artifact_id(dataset_stem: RelativePath, seed: SeedValue) -> ArtifactIdentity:
    return f"full-emhi-fit.{dataset_stem}.seed-{seed}"


def _evaluation_artifact_id(
    experiment_name: ExperimentName,
    execution_role: ExecutionRole,
    method_name: MethodName,
    seed: SeedValue,
) -> ArtifactIdentity:
    return (
        f"evaluation.{experiment_name.value}.{execution_role.value}."
        f"{_method_slug(method_name)}.seed-{seed}"
    )


def _dependency_fingerprint(
    loaded: LoadedScientificConfiguration,
    method_name: MethodName,
    maximum_order: CoalitionOrder | None,
    target_local_pfa: FalseAlarmRate,
    required_paths: tuple[Path, ...],
) -> MaterialDependencyFingerprint:
    method_digest = payload_digest(
        cast(
            YamlNode,
            {
                "method": method_name.value,
                "maximum_order": None if maximum_order is None else int(maximum_order),
                "target_local_pfa": target_local_pfa,
            },
        )
    )
    return material_fingerprint(
        loaded.material_digest,
        (method_digest,) + tuple(file_sha256(path) for path in required_paths),
    )


def _calibration_payload(calibration: OperationalCalibration) -> YamlNode:
    global_point = calibration.global_operating_point
    return {
        "global": {
            "threshold": global_point.threshold,
            "calibration_false_stop_counts": list(global_point.calibration_false_stop_counts),
            "calibration_horizon_count": global_point.calibration_horizon_count,
            "heldout_false_stop_count": global_point.heldout_false_stop_count,
            "heldout_horizon_count": global_point.heldout_horizon_count,
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


def _campaign_payloads(
    loaded: LoadedScientificConfiguration,
    scores: DetectorScoreArtifactRecord,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    campaigns: CampaignRegistryRecord,
    calibration: OperationalCalibration,
    maximum_order: CoalitionOrder | None,
) -> tuple[YamlNode, ...]:
    rows: list[YamlNode] = []
    threshold = calibration.global_operating_point.threshold
    for campaign in campaigns.campaigns:
        started = perf_counter()
        trajectory = campaign_trajectory(
            loaded.values,
            ranks,
            fit,
            campaign,
            maximum_order,
        )
        elapsed: RuntimeSeconds = perf_counter() - started
        evaluation_epochs = tuple(row.epoch_index for row in trajectory.epochs)
        global_stop = None if threshold is None else global_stop_epoch(trajectory, threshold)
        local_stops = local_stop_epochs(
            scores,
            calibration.local_operating_points,
            evaluation_epochs,
        )
        odi = odi_evaluation_record(global_stop, local_stops)
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
        rows.append(
            {
                "start_epoch": campaign.start_epoch,
                "end_epoch": campaign.end_epoch,
                "participating_client_ids": list(campaign.participating_client_ids),
                "global_stop_epoch": global_stop,
                "local_stop_epochs": list(local_stops),
                "local_min_stop_epoch": earliest_local,
                "strict_odi": odi.indicator,
                "statistical_lead_epochs": statistical,
                "operational_lead_epochs": operational,
                "global_detected_within_horizon": odi.global_detection_indicator,
                "local_detected_within_horizon": 0 if earliest_local is None else 1,
                "decisive_order": None if decisive is None else int(decisive),
                "context_coverage": coverage,
                "abstention_rate": 1.0 - coverage,
                "server_latency_seconds": elapsed,
                "end_to_end_latency_seconds": elapsed,
            }
        )
    return tuple(rows)


def _heldout_payloads(
    loaded: LoadedScientificConfiguration,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    partitions: BenignPartitionRecord,
    calibration: OperationalCalibration,
    maximum_order: CoalitionOrder | None,
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
        maximum_order,
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
        }
        for index, (horizon, trajectory, stop_epoch) in enumerate(records)
    )


def _odi_values(campaign_payloads: tuple[YamlNode, ...]) -> tuple[FiniteFloat, ...]:
    values: list[FiniteFloat] = []
    for payload in campaign_payloads:
        if not isinstance(payload, dict):
            raise ValueError("campaign evaluation payload must be a mapping")
        value = payload.get("strict_odi")
        if not isinstance(value, int):
            raise ValueError("campaign evaluation requires strict ODI indicator")
        indicator: OdiIndicator = value
        values.append(float(indicator))
    return tuple(values)


def execute_emhi_method_seed_cell(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    execution_role: ExecutionRole,
    method_name: MethodName,
    seed: SeedValue,
    score_path: Path,
    rank_path: Path,
    fit_path: Path,
    split_path: Path,
    partitions_path: Path,
    campaigns_path: Path,
    target_local_pfa: FalseAlarmRate,
) -> RealMethodSeedExecution:
    started = perf_counter()
    maximum_order = maximum_order_for_method(method_name)
    required_paths = (
        score_path,
        rank_path,
        fit_path,
        split_path,
        partitions_path,
        campaigns_path,
    )
    dependency_fingerprint = _dependency_fingerprint(
        loaded,
        method_name,
        maximum_order,
        target_local_pfa,
        required_paths,
    )
    scores = DetectorScoreArtifactRecord.model_validate_json(score_path.read_bytes())
    ranks = MarginalRankArtifactRecord.model_validate_json(rank_path.read_bytes())
    fit = EMHIFitArtifactRecord.model_validate_json(fit_path.read_bytes())
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    partitions = BenignPartitionRecord.model_validate_json(partitions_path.read_bytes())
    campaigns = CampaignRegistryRecord.model_validate_json(campaigns_path.read_bytes())
    calibration = calibrate_operating_points(
        loaded.values,
        scores,
        ranks,
        fit,
        split.nuisance_fit_epochs,
        partitions,
        target_local_pfa,
        maximum_order,
    )
    campaign_payloads = _campaign_payloads(
        loaded,
        scores,
        ranks,
        fit,
        campaigns,
        calibration,
        maximum_order,
    )
    heldout_payloads = _heldout_payloads(
        loaded,
        ranks,
        fit,
        partitions,
        calibration,
        maximum_order,
    )
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    method_slug = _method_slug(method_name)
    staging = layout.roots.outputs_root / "cache" / "staging"
    evaluation_id = _evaluation_artifact_id(
        experiment_name,
        execution_role,
        method_name,
        seed,
    )
    raw_path = (
        root
        / "evaluations"
        / "raw"
        / execution_role.value
        / method_slug
        / f"seed-{seed}.json"
    )
    raw_payload: YamlNode = {
        "artifact_id": evaluation_id,
        "experiment_name": experiment_name.value,
        "execution_role": execution_role.value,
        "dataset_name": fit.dataset_name.value,
        "method_name": method_name.value,
        "seed": seed,
        "dependency_fingerprint": dependency_fingerprint,
        "calibration": _calibration_payload(calibration),
        "heldout_benign": list(heldout_payloads),
        "campaigns": list(campaign_payloads),
    }
    raw_hash = write_atomic_json(raw_path, raw_payload, staging)
    odi_values = _odi_values(campaign_payloads)
    if not odi_values:
        raise ValueError("real-data ODI evaluation requires at least one eligible campaign")
    summary = build_seed_summary(
        experiment_name=experiment_name,
        execution_role=execution_role,
        method_name=method_name,
        reference_method_name=None,
        metric_name="strict_odi_rate",
        seed=seed,
        method_values=odi_values,
        reference_values=None,
        source_evaluation_ids=(evaluation_id,),
        dependency_fingerprint=dependency_fingerprint,
    )
    summary_path = (
        root
        / "metrics"
        / "seed-summaries"
        / execution_role.value
        / method_slug
        / f"seed-{seed}.json"
    )
    summary_hash = write_atomic_json(
        summary_path,
        cast(YamlNode, summary.model_dump(mode="json")),
        staging,
    )
    dataset_stem = dataset_directory_stem(fit.dataset_name)
    upstream_ids = (
        _score_artifact_id(dataset_stem, seed),
        _rank_artifact_id(dataset_stem, seed),
        _fit_artifact_id(dataset_stem, seed),
        layer_artifact_id(fit.dataset_name, PreprocessingLayer.PARTITIONS),
        layer_artifact_id(fit.dataset_name, PreprocessingLayer.CAMPAIGN_REGISTRY),
    )
    completion = CompletionRecord(
        state=ExperimentState.COMPLETED,
        mandatory_output_paths=(
            raw_path.relative_to(repository).as_posix(),
            summary_path.relative_to(repository).as_posix(),
        ),
        mandatory_output_hashes=(raw_hash, summary_hash),
    )
    elapsed: RuntimeSeconds = perf_counter() - started
    cell = ScientificCellRecord(
        experiment_name=experiment_name,
        execution_role=execution_role,
        semantic_cell_path=f"{execution_role.value}/{method_slug}/seed-{seed}",
        method_name=method_name,
        seed=seed,
        state=ExperimentState.COMPLETED,
        material_digest=loaded.material_digest,
        selected_client_ids=fit.selected_client_ids,
        upstream_artifact_ids=upstream_ids,
        dependency_fingerprint=dependency_fingerprint,
        runtime_seconds=elapsed,
        peak_rss_bytes=0,
        application_payload_bytes=len(raw_path.read_bytes()),
        completion_record=completion,
    )
    cell_path = (
        root
        / "provenance"
        / "dependencies"
        / f"cell-{execution_role.value}-{method_slug}-seed-{seed}.json"
    )
    write_atomic_json(cell_path, cast(YamlNode, cell.model_dump(mode="json")), staging)
    return RealMethodSeedExecution(
        raw_evaluation_path=raw_path,
        cell_path=cell_path,
        seed_summary_path=summary_path,
        seed_summary=summary,
        state=ExperimentState.COMPLETED,
    )
