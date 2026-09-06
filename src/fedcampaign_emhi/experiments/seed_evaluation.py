from collections.abc import Mapping
from pathlib import Path
from time import perf_counter
from typing import cast

from fedcampaign_emhi.analysis.results import (
    build_seed_summary,
)
from fedcampaign_emhi.artifacts.provenance import (
    calibration_threshold_boundary_digest,
    campaign_evaluation_boundary_digest,
    material_fingerprint,
    nuisance_context_boundary_digest,
)
from fedcampaign_emhi.artifacts.records import (
    BenignPartitionRecord,
    CampaignRegistryRecord,
    ClientDetectorScoreStream,
    CompletionRecord,
    ContextEstimatorSensitivityCellRecord,
    ContextEstimatorSensitivityMetrics,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
    EMHIFitArtifactRecord,
    MarginalRankArtifactRecord,
    PreparedDatasetRecord,
    ScientificCellRecord,
)
from fedcampaign_emhi.artifacts.storage import (
    build_artifact_layout,
    detector_score_artifact_id,
    emhi_fit_artifact_id,
    file_sha256,
    layer_artifact_id,
    marginal_rank_artifact_id,
    method_artifact_stem,
    payload_digest,
    write_atomic_json,
)
from fedcampaign_emhi.comparators.conditioning import (
    CONDITIONED_COMPARATOR_METHODS,
    comparator_panel,
    condition_epoch_ranks,
    conditioned_comparator_order,
    fit_comparator_conditioning,
)
from fedcampaign_emhi.comparators.federated import fit_federated_autoencoder
from fedcampaign_emhi.comparators.runtime import (
    fit_comparator_state,
    resolve_comparator_scoring_method,
    score_comparator_ranks,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.detection import (
    score_fitted_client_detector,
    score_stream_isolation_check,
)
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
    DetectorFamily,
    ExecutionRole,
    ExperimentName,
    ExperimentState,
    MethodName,
    PartitionRole,
    PreprocessingLayer,
)
from fedcampaign_emhi.domain.types import (
    BasisSize,
    Boolean,
    CellCount,
    ContextCoverage,
    CusumState,
    DetectorScore,
    EpochIndexValue,
    FalseAlarmRate,
    FeatureValue,
    OdiIndicator,
    OdiRateAdvantage,
    OperationalLeadEpochs,
    RankValue,
    RecordCount,
    RelativePath,
    RidgePenalty,
    RuntimeSeconds,
    SeedDerivationIdentity,
    SeedValue,
    ThresholdValue,
)
from fedcampaign_emhi.emhi.calibration import build_emhi_fit_artifact
from fedcampaign_emhi.emhi.evidence import (
    operational_evidence_factor,
    operational_norm_reference_quantile,
)
from fedcampaign_emhi.emhi.sequential import next_global_state
from fedcampaign_emhi.emhi.structure import build_marginal_rank_artifact
from fedcampaign_emhi.emhi.thresholds import (
    clopper_pearson_one_sided_upper_bound,
    select_calibrated_threshold,
)
from fedcampaign_emhi.evaluation.metrics import (
    earliest_local_stop,
    false_campaigns_per_ten_thousand_benign_epochs,
    seed_level_odi_rate,
    strict_odi_outcome,
)
from fedcampaign_emhi.evaluation.scalability import (
    resident_set_bytes,
)
from fedcampaign_emhi.evaluation.sequential import (
    TrajectoryCache,
    calibrate_client_local_operating_point,
    calibrate_operating_points,
    local_stop_epochs,
    operational_lead,
    statistical_lead,
)
from fedcampaign_emhi.experiments.execution import (
    as_mapping,
    campaign_dataset,
    campaigns_logger,
    emhi_method_specification,
    experiment_contract,
)
from fedcampaign_emhi.experiments.registry import (
    ExperimentContract,
)
from fedcampaign_emhi.experiments.seed_materialization import (
    build_campaign_rows,
    build_heldout_rows,
    calibration_payload,
    evaluation_artifact_id,
    local_pfa_target,
    materialize_detector_scores_with_retry,
    materialize_emhi_fit_with_retry,
    materialize_marginal_ranks_with_retry,
    preprocessing_paths,
)
from fedcampaign_emhi.experiments.technical_retry import with_technical_retry
from fedcampaign_emhi.runtime import derive_component_seed


def _evaluate_emhi_seed_cell(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    execution_role: ExecutionRole,
    method_name: MethodName,
    seed: SeedValue,
    score_path: Path,
    rank_path: Path,
    fit_path: Path,
) -> Path:
    started = perf_counter()
    _inventory_path, _prepared_path, split_path, partitions_path, campaigns_path = (
        preprocessing_paths(loaded, repository, campaign_dataset(loaded, experiment_name))
    )
    target_local_pfa = local_pfa_target(loaded, experiment_name)
    method_digest = payload_digest(
        cast(
            YamlNode,
            {
                "method_name": method_name.value,
                "target_local_pfa": target_local_pfa,
                "execution_role": execution_role.value,
                "seed": seed,
            },
        )
    )
    required_paths = (
        score_path,
        rank_path,
        fit_path,
        split_path,
        partitions_path,
        campaigns_path,
    )
    fingerprint = material_fingerprint(
        calibration_threshold_boundary_digest(loaded.values),
        (
            method_digest,
            campaign_evaluation_boundary_digest(loaded.values),
            *(file_sha256(path) for path in required_paths),
        ),
    )
    scores = DetectorScoreArtifactRecord.model_validate_json(score_path.read_bytes())
    ranks = MarginalRankArtifactRecord.model_validate_json(rank_path.read_bytes())
    fit = EMHIFitArtifactRecord.model_validate_json(fit_path.read_bytes())
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    partitions = BenignPartitionRecord.model_validate_json(partitions_path.read_bytes())
    campaigns = CampaignRegistryRecord.model_validate_json(campaigns_path.read_bytes())
    trajectory_cache = TrajectoryCache()
    calibration = calibrate_operating_points(
        loaded.values,
        scores,
        ranks,
        fit,
        split.nuisance_fit_epochs,
        partitions,
        target_local_pfa,
        trajectory_cache=trajectory_cache,
    )
    campaign_rows, odi_values = build_campaign_rows(
        loaded,
        scores,
        ranks,
        fit,
        campaigns,
        calibration,
    )
    heldout_rows = build_heldout_rows(loaded, ranks, fit, partitions, calibration, trajectory_cache)
    heldout_maps = tuple(as_mapping(row) for row in heldout_rows)
    heldout_false_stops = sum(cast(int, row["false_campaign"]) for row in heldout_maps)
    heldout_epochs = sum(len(horizon.epoch_indexes) for horizon in partitions.heldout_horizons)
    false_campaign_rate = (
        None
        if heldout_epochs <= 0
        else false_campaigns_per_ten_thousand_benign_epochs(heldout_false_stops, heldout_epochs)
    )
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    staging = layout.roots.outputs_root / "cache" / "staging"
    method_slug = method_artifact_stem(method_name)
    evaluation_id = evaluation_artifact_id(
        experiment_name,
        execution_role,
        method_name,
        seed,
    )
    raw_path = (
        root / "evaluations" / "raw" / execution_role.value / method_slug / f"seed-{seed}.json"
    )
    raw_payload: YamlNode = {
        "artifact_id": evaluation_id,
        "experiment_name": experiment_name.value,
        "execution_role": execution_role.value,
        "dataset_name": fit.dataset_name.value,
        "method_name": method_name.value,
        "seed": seed,
        "dependency_fingerprint": fingerprint,
        "calibration": calibration_payload(calibration),
        PartitionRole.HELDOUT_BENIGN.value: list(heldout_rows),
        "campaigns": list(campaign_rows),
        "seed_strict_odi_rate": None if not odi_values else seed_level_odi_rate(odi_values),
        "false_campaigns_per_ten_thousand_benign_epochs": false_campaign_rate,
    }
    raw_hash = write_atomic_json(raw_path, raw_payload, staging)
    output_paths = [raw_path.relative_to(repository).as_posix()]
    output_hashes = [raw_hash]
    if odi_values:
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
            dependency_fingerprint=fingerprint,
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
        output_paths.append(summary_path.relative_to(repository).as_posix())
        output_hashes.append(summary_hash)
    dataset_name = fit.dataset_name
    upstream_ids = (
        detector_score_artifact_id(dataset_name, seed),
        marginal_rank_artifact_id(dataset_name, seed),
        emhi_fit_artifact_id(dataset_name, seed, method_name),
        layer_artifact_id(dataset_name, PreprocessingLayer.PARTITIONS),
        layer_artifact_id(dataset_name, PreprocessingLayer.CAMPAIGN_REGISTRY),
    )
    elapsed: RuntimeSeconds = perf_counter() - started
    completion = CompletionRecord(
        state=ExperimentState.COMPLETED,
        mandatory_output_paths=tuple(output_paths),
        mandatory_output_hashes=tuple(output_hashes),
    )
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
        dependency_fingerprint=fingerprint,
        runtime_seconds=elapsed,
        peak_rss_bytes=resident_set_bytes(),
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
    return cell_path


def role_seeds(
    loaded: LoadedScientificConfiguration,
    role: ExecutionRole,
) -> tuple[SeedValue, ...]:
    if role is ExecutionRole.CONFIRMATORY:
        return loaded.values.randomness.real_confirmatory_roots
    return loaded.values.randomness.real_development_roots


def materialize_not_tested_real_cell(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    execution_role: ExecutionRole,
    method_name: MethodName | None,
    seed: SeedValue,
) -> Path:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    staging = layout.roots.outputs_root / "cache" / "staging"
    method_slug = (
        "coordinate-validation" if method_name is None else method_artifact_stem(method_name)
    )
    raw_path = (
        root / "evaluations" / "raw" / execution_role.value / method_slug / f"seed-{seed}.json"
    )
    fingerprint = material_fingerprint(
        campaign_evaluation_boundary_digest(loaded.values),
        (
            payload_digest(
                cast(
                    YamlNode,
                    {
                        "method": None if method_name is None else method_name.value,
                        "seed": seed,
                    },
                )
            ),
        ),
    )
    payload: YamlNode = {
        "experiment_name": experiment_name.value,
        "execution_role": execution_role.value,
        "method_name": None if method_name is None else method_name.value,
        "seed": seed,
        "scientific_outcome": "Not Tested",
        "reason": "no eligible raw records were available after deterministic preprocessing",
        "dependency_fingerprint": fingerprint,
        "campaigns": [],
        PartitionRole.HELDOUT_BENIGN.value: [],
    }
    raw_hash = write_atomic_json(raw_path, payload, staging)
    cell = ScientificCellRecord(
        experiment_name=experiment_name,
        execution_role=execution_role,
        semantic_cell_path=f"{execution_role.value}/{method_slug}/seed-{seed}",
        method_name=method_name,
        seed=seed,
        state=ExperimentState.COMPLETED,
        material_digest=loaded.material_digest,
        selected_client_ids=(),
        upstream_artifact_ids=(),
        dependency_fingerprint=fingerprint,
        runtime_seconds=0.0,
        peak_rss_bytes=0,
        application_payload_bytes=len(raw_path.read_bytes()),
        completion_record=CompletionRecord(
            state=ExperimentState.COMPLETED,
            mandatory_output_paths=(raw_path.relative_to(repository).as_posix(),),
            mandatory_output_hashes=(raw_hash,),
        ),
    )
    cell_path = (
        root
        / "provenance"
        / "dependencies"
        / f"cell-{execution_role.value}-{method_slug}-seed-{seed}.json"
    )
    write_atomic_json(cell_path, cast(YamlNode, cell.model_dump(mode="json")), staging)
    return cell_path


def _fedavg_autoencoder_ranks(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    seed: SeedValue,
    split: DatasetSplitRecord,
    detector_scores: DetectorScoreArtifactRecord,
) -> MarginalRankArtifactRecord:
    _inventory_path, prepared_path, _split_path, _partitions_path, _campaigns_path = (
        preprocessing_paths(loaded, repository, dataset_name)
    )
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    client_fit_rows: list[tuple[tuple[FeatureValue, ...], ...]] = []
    client_all_rows: list[tuple[tuple[FeatureValue, ...], ...]] = []
    client_epoch_indexes: list[tuple[EpochIndexValue, ...]] = []
    for client_id in split.selected_client_ids:
        client_rows = tuple(row for row in prepared.epochs if row.client_id == client_id)
        fit_rows = tuple(
            row.feature_values
            for row in client_rows
            if row.epoch_index in split.detector_fit_epochs
        )
        if not fit_rows:
            raise ValueError(f"selected client {client_id} has no benign detector-fit rows")
        client_fit_rows.append(fit_rows)
        client_all_rows.append(tuple(row.feature_values for row in client_rows))
        client_epoch_indexes.append(tuple(row.epoch_index for row in client_rows))
    fedavg_seed = derive_component_seed(
        SeedDerivationIdentity(
            base_seed=seed,
            component_name="fedavg-autoencoder-fit",
            dataset=dataset_name,
            client_ids=split.selected_client_ids,
            coalition_ids=(),
            condition_coordinates=(),
        )
    )
    fedavg_config = loaded.values.comparators.fedavg_autoencoder
    detector_config = loaded.values.detectors.autoencoder
    if len(detector_config.betas) != 2:
        raise ValueError("autoencoder requires exactly two Adam beta coefficients")
    fitted = fit_federated_autoencoder(
        tuple(client_fit_rows),
        split.selected_client_ids,
        fedavg_config.rounds,
        fedavg_config.local_epochs_per_round,
        fedavg_config.client_participation_fraction,
        detector_config.learning_rate,
        detector_config.betas[0],
        detector_config.betas[1],
        detector_config.optimizer_epsilon,
        detector_config.weight_decay,
        detector_config.batch_size,
        fedavg_seed,
    )
    streams: list[ClientDetectorScoreStream] = []
    for client_id, all_rows, epoch_indexes in zip(
        split.selected_client_ids, client_all_rows, client_epoch_indexes, strict=True
    ):
        scores = score_fitted_client_detector(fitted, all_rows)
        score_stream_isolation_check(len(scores), len(epoch_indexes))
        streams.append(
            ClientDetectorScoreStream(
                client_id=client_id,
                detector_family=DetectorFamily.AUTOENCODER,
                detector_seed=fedavg_seed,
                epoch_indexes=epoch_indexes,
                scores=scores,
            )
        )
    fedavg_scores = DetectorScoreArtifactRecord(
        dataset_name=dataset_name,
        root_seed=seed,
        selected_client_ids=split.selected_client_ids,
        client_streams=tuple(streams),
        dependency_fingerprint=material_fingerprint(
            payload_digest(
                cast(
                    YamlNode,
                    {
                        "component": "fedavg-autoencoder-scores",
                        "dataset": dataset_name.value,
                        "seed": seed,
                        "selected_client_ids": list(split.selected_client_ids),
                    },
                )
            ),
            (detector_scores.dependency_fingerprint,),
        ),
    )
    return build_marginal_rank_artifact(
        fedavg_scores,
        split.nuisance_fit_epochs,
        loaded.values.context.rank_clip_epsilon,
        fedavg_scores.dependency_fingerprint,
    )


def comparator_epoch_scores(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    ranks: MarginalRankArtifactRecord,
    method_name: MethodName,
    nuisance_fit_epochs: tuple[EpochIndexValue, ...],
) -> tuple[tuple[EpochIndexValue, DetectorScore], ...]:
    streams = tuple(
        (
            stream.client_id,
            dict(zip(stream.epoch_indexes, stream.ranks, strict=True)),
        )
        for stream in ranks.client_streams
    )
    if not streams:
        return ()
    epoch_sets: tuple[set[EpochIndexValue], ...] = tuple(
        set(epoch_rank_map) for _client_id, epoch_rank_map in streams
    )
    common_epoch_set: set[EpochIndexValue] = set(epoch_sets[0])
    for epoch_set in epoch_sets[1:]:
        common_epoch_set.intersection_update(epoch_set)
    common_epochs: list[EpochIndexValue] = sorted(common_epoch_set)
    scoring_method = resolve_comparator_scoring_method(loaded, repository, method_name)
    triple_methods = {
        MethodName.CONDITIONAL_PAIR_DEPENDENCE,
        MethodName.EXCLUSION_MATCHED_LANCASTER_TRIPLE,
        MethodName.CONNECTED_INFORMATION_REFERENCE,
        MethodName.D_VINE_CONDITIONAL_REFERENCE,
        MethodName.CONDITIONAL_LOG_LINEAR_REFERENCE,
    }

    def _full_row_for_epoch(epoch: EpochIndexValue) -> tuple[RankValue, ...]:
        return tuple(epoch_rank_map[epoch] for _client_id, epoch_rank_map in streams)

    def _row_for_epoch(epoch: EpochIndexValue) -> tuple[RankValue, ...]:
        values = _full_row_for_epoch(epoch)
        return values[:3] if scoring_method in triple_methods else values

    conditioned = scoring_method in CONDITIONED_COMPARATOR_METHODS
    nuisance_epoch_set = set(nuisance_fit_epochs)
    if conditioned:
        native_order = conditioned_comparator_order(scoring_method)
        if native_order is None:
            raise ValueError(f"{scoring_method.value} has no conditioned native order")
        panel = comparator_panel(
            tuple(common_epochs),
            tuple(_full_row_for_epoch(epoch) for epoch in common_epochs),
        )
        model = fit_comparator_conditioning(
            loaded.values,
            ranks.dataset_name,
            panel,
            tuple(epoch for epoch in common_epochs if epoch in nuisance_epoch_set),
            int(native_order),
            ranks.selected_client_ids,
        )
        if model is None:
            return ()
        nuisance_conditioned = tuple(
            conditioned_row
            for epoch in common_epochs
            if epoch in nuisance_epoch_set
            and (conditioned_row := condition_epoch_ranks(loaded.values, panel, epoch, model))
            is not None
        )
        fitted_state = fit_comparator_state(scoring_method, nuisance_conditioned, loaded.values)
        scores: list[tuple[EpochIndexValue, DetectorScore]] = []
        cusum_state: tuple[CusumState, ...] = ()
        for epoch in common_epochs:
            conditioned_row = condition_epoch_ranks(loaded.values, panel, epoch, model)
            if conditioned_row is None:
                continue
            score, cusum_state = score_comparator_ranks(
                scoring_method,
                conditioned_row,
                loaded.values,
                cusum_state,
                fitted_state,
            )
            scores.append((epoch, score))
        return tuple(scores)
    nuisance_rows = tuple(
        _row_for_epoch(epoch) for epoch in common_epochs if epoch in nuisance_epoch_set
    )
    fitted_state = (
        fit_comparator_state(scoring_method, nuisance_rows, loaded.values)
        if nuisance_rows
        else None
    )
    scores: list[tuple[EpochIndexValue, DetectorScore]] = []
    cusum_state: tuple[CusumState, ...] = ()
    for epoch in common_epochs:
        inputs = _row_for_epoch(epoch)
        score, cusum_state = score_comparator_ranks(
            scoring_method,
            inputs,
            loaded.values,
            cusum_state,
            fitted_state,
        )
        scores.append((epoch, score))
    return tuple(scores)


def comparator_evidence_scores(
    loaded: LoadedScientificConfiguration,
    raw_scores: tuple[tuple[EpochIndexValue, DetectorScore], ...],
    nuisance_epochs: tuple[EpochIndexValue, ...],
) -> tuple[tuple[EpochIndexValue, DetectorScore], ...]:
    if not raw_scores:
        return ()
    nuisance_scores = tuple(score for epoch, score in raw_scores if epoch in nuisance_epochs)
    if not nuisance_scores:
        raise ValueError("comparator evidence requires nuisance-fit scores")
    nuisance_mean = sum(nuisance_scores) / len(nuisance_scores)
    nuisance_deviation = (
        sum((score - nuisance_mean) ** 2 for score in nuisance_scores) / len(nuisance_scores)
    ) ** 0.5
    floor = loaded.values.numerics.metric_denominator_floor
    if nuisance_deviation <= floor:
        return ()
    standardized = tuple(
        (epoch, abs((score - nuisance_mean) / nuisance_deviation)) for epoch, score in raw_scores
    )
    reference = operational_norm_reference_quantile(
        tuple((score,) for epoch, score in standardized if epoch in nuisance_epochs),
        loaded.values.comparators.common_calibration.nuisance_reference_quantile,
    )
    return tuple(
        (
            epoch,
            operational_evidence_factor(
                (score,),
                reference,
                floor,
                loaded.values.evidence.clip_bound,
                loaded.values.evidence.bet_lambda,
            ),
        )
        for epoch, score in standardized
    )


def comparator_stop(
    evidence_scores: tuple[tuple[EpochIndexValue, DetectorScore], ...],
    epochs: tuple[EpochIndexValue, ...],
    threshold: ThresholdValue | None,
) -> EpochIndexValue | None:
    if threshold is None:
        return None
    epoch_scores = dict(evidence_scores)
    state = 0.0
    for epoch in epochs:
        factor = epoch_scores.get(epoch)
        if factor is None:
            continue
        state = next_global_state(state, factor)
        if state >= threshold:
            return epoch
    return None


def calibrate_comparator_operating_point(
    loaded: LoadedScientificConfiguration,
    evidence_scores: tuple[tuple[EpochIndexValue, DetectorScore], ...],
    partitions: BenignPartitionRecord,
) -> tuple[
    ThresholdValue | None, tuple[RecordCount, ...], RecordCount, RecordCount, FalseAlarmRate | None
]:
    if not evidence_scores:
        return None, (), len(partitions.calibration_horizons), 0, None
    calibration_horizons = partitions.calibration_horizons
    heldout_horizons = partitions.heldout_horizons
    candidates = loaded.values.evidence.calibrated_finite_horizon.threshold_candidates
    calibration_counts = tuple(
        sum(
            comparator_stop(evidence_scores, horizon.epoch_indexes, threshold) is not None
            for horizon in calibration_horizons
        )
        for threshold in candidates
    )
    selected = select_calibrated_threshold(
        candidates,
        calibration_counts,
        len(calibration_horizons),
        loaded.values.evidence.calibrated_finite_horizon.calibration_confidence,
        loaded.values.evidence.calibrated_finite_horizon.target_pfa,
    )
    if selected is None:
        return None, calibration_counts, len(calibration_horizons), 0, None
    heldout_count = sum(
        comparator_stop(evidence_scores, horizon.epoch_indexes, selected) is not None
        for horizon in heldout_horizons
    )
    upper = (
        None
        if not heldout_horizons
        else clopper_pearson_one_sided_upper_bound(
            heldout_count,
            len(heldout_horizons),
            loaded.values.evidence.calibrated_finite_horizon.calibration_confidence,
        )
    )
    return selected, calibration_counts, len(calibration_horizons), heldout_count, upper


def _evaluate_comparator_seed_cell(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    execution_role: ExecutionRole,
    method_name: MethodName,
    seed: SeedValue,
    score_path: Path,
    rank_path: Path,
) -> Path:
    cell_started = perf_counter()
    dataset_name = campaign_dataset(loaded, experiment_name)
    _inventory_path, _prepared_path, split_path, partitions_path, campaigns_path = (
        preprocessing_paths(loaded, repository, dataset_name)
    )
    ranks = MarginalRankArtifactRecord.model_validate_json(rank_path.read_bytes())
    detector_scores = DetectorScoreArtifactRecord.model_validate_json(score_path.read_bytes())
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    partitions = BenignPartitionRecord.model_validate_json(partitions_path.read_bytes())
    campaigns = CampaignRegistryRecord.model_validate_json(campaigns_path.read_bytes())
    scoring_ranks = (
        _fedavg_autoencoder_ranks(loaded, repository, dataset_name, seed, split, detector_scores)
        if method_name is MethodName.FEDAVG_AUTOENCODER_REFERENCE
        else ranks
    )
    raw_scores = comparator_epoch_scores(
        loaded, repository, scoring_ranks, method_name, split.nuisance_fit_epochs
    )
    scores = comparator_evidence_scores(loaded, raw_scores, split.nuisance_fit_epochs)
    (
        threshold,
        calibration_false_stop_counts,
        calibration_horizon_count,
        heldout_false_stop_count,
        heldout_upper_pfa,
    ) = calibrate_comparator_operating_point(loaded, scores, partitions)
    local_operating_points = tuple(
        calibrate_client_local_operating_point(
            loaded.values,
            detector_scores,
            client_id,
            split.nuisance_fit_epochs,
            partitions,
            local_pfa_target(loaded, experiment_name),
        )
        for client_id in detector_scores.selected_client_ids
    )
    campaign_rows: list[YamlNode] = []
    odi_values: list[OdiRateAdvantage] = []
    for campaign in campaigns.campaigns:
        started = perf_counter()
        epochs = tuple(range(campaign.start_epoch, campaign.end_epoch + 1))
        stop_epoch = comparator_stop(scores, epochs, threshold)
        elapsed: RuntimeSeconds = perf_counter() - started
        local_stops = local_stop_epochs(detector_scores, local_operating_points, epochs)
        odi = strict_odi_outcome(stop_epoch, local_stops)
        earliest_local = earliest_local_stop(local_stops)
        statistical = (
            None
            if stop_epoch is None or earliest_local is None
            else statistical_lead(earliest_local, stop_epoch)
        )
        operational = (
            None
            if stop_epoch is None or earliest_local is None
            else operational_lead(
                earliest_local,
                stop_epoch,
                elapsed,
                loaded.values.time.real_data_epoch_seconds,
            )
        )
        indicator: OdiIndicator = odi.indicator
        odi_values.append(indicator)
        campaign_rows.append(
            {
                "start_epoch": campaign.start_epoch,
                "end_epoch": campaign.end_epoch,
                "participating_client_ids": list(campaign.participating_client_ids),
                "global_stop_epoch": stop_epoch,
                "local_stop_epochs": list(local_stops),
                "local_min_stop_epoch": earliest_local,
                "strict_odi": indicator,
                "statistical_lead_epochs": statistical,
                "operational_lead_epochs": operational,
                "global_detected_within_horizon": odi.global_detection_indicator,
                "local_detected_within_horizon": 0 if earliest_local is None else 1,
                "context_coverage": 1.0,
                "abstention_rate": 0.0,
                "comparator_score_threshold": threshold,
            }
        )
    heldout_rows: list[YamlNode] = []
    for index, horizon in enumerate(partitions.heldout_horizons):
        stop_epoch = comparator_stop(scores, horizon.epoch_indexes, threshold)
        heldout_rows.append(
            {
                "split_role": PartitionRole.HELDOUT_BENIGN.value,
                "horizon_index": index,
                "start_epoch": horizon.start_epoch,
                "threshold": threshold,
                "false_campaign": int(stop_epoch is not None),
                "first_stop_epoch": stop_epoch,
                "context_coverage": 1.0,
                "abstention_rate": 0.0,
            }
        )
    method_digest = payload_digest(cast(YamlNode, {"method_name": method_name.value, "seed": seed}))
    fingerprint = material_fingerprint(
        calibration_threshold_boundary_digest(loaded.values),
        (
            method_digest,
            campaign_evaluation_boundary_digest(loaded.values),
            file_sha256(score_path),
            file_sha256(rank_path),
            file_sha256(split_path),
            file_sha256(partitions_path),
        ),
    )
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    staging = layout.roots.outputs_root / "cache" / "staging"
    evaluation_id = evaluation_artifact_id(experiment_name, execution_role, method_name, seed)
    raw_path = (
        root
        / "evaluations"
        / "raw"
        / execution_role.value
        / method_artifact_stem(method_name)
        / f"seed-{seed}.json"
    )
    raw_payload: YamlNode = {
        "artifact_id": evaluation_id,
        "experiment_name": experiment_name.value,
        "execution_role": execution_role.value,
        "dataset_name": dataset_name.value,
        "method_name": method_name.value,
        "seed": seed,
        "dependency_fingerprint": fingerprint,
        "calibration": {
            "global": {
                "threshold": threshold,
                "calibration_false_stop_counts": list(calibration_false_stop_counts),
                "calibration_horizon_count": calibration_horizon_count,
                "heldout_false_stop_count": heldout_false_stop_count,
                "heldout_horizon_count": len(partitions.heldout_horizons),
                "heldout_upper_pfa": heldout_upper_pfa,
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
                for point in local_operating_points
            ],
        },
        PartitionRole.HELDOUT_BENIGN.value: heldout_rows,
        "campaigns": campaign_rows,
    }
    raw_hash = write_atomic_json(raw_path, raw_payload, staging)
    output_paths = [raw_path.relative_to(repository).as_posix()]
    output_hashes = [raw_hash]
    if odi_values:
        summary = build_seed_summary(
            experiment_name=experiment_name,
            execution_role=execution_role,
            method_name=method_name,
            reference_method_name=None,
            metric_name="strict_odi_rate",
            seed=seed,
            method_values=tuple(odi_values),
            reference_values=None,
            source_evaluation_ids=(evaluation_id,),
            dependency_fingerprint=fingerprint,
        )
        summary_path = (
            root
            / "metrics"
            / "seed-summaries"
            / execution_role.value
            / method_artifact_stem(method_name)
            / f"seed-{seed}.json"
        )
        summary_hash = write_atomic_json(
            summary_path,
            cast(YamlNode, summary.model_dump(mode="json")),
            staging,
        )
        output_paths.append(summary_path.relative_to(repository).as_posix())
        output_hashes.append(summary_hash)
    cell = ScientificCellRecord(
        experiment_name=experiment_name,
        execution_role=execution_role,
        semantic_cell_path=f"{execution_role.value}/{method_artifact_stem(method_name)}/seed-{seed}",
        method_name=method_name,
        seed=seed,
        state=ExperimentState.COMPLETED,
        material_digest=loaded.material_digest,
        selected_client_ids=ranks.selected_client_ids,
        upstream_artifact_ids=(
            marginal_rank_artifact_id(dataset_name, seed),
            layer_artifact_id(dataset_name, PreprocessingLayer.PARTITIONS),
            layer_artifact_id(dataset_name, PreprocessingLayer.CAMPAIGN_REGISTRY),
        ),
        dependency_fingerprint=fingerprint,
        runtime_seconds=perf_counter() - cell_started,
        peak_rss_bytes=resident_set_bytes(),
        application_payload_bytes=len(raw_path.read_bytes()),
        completion_record=CompletionRecord(
            state=ExperimentState.COMPLETED,
            mandatory_output_paths=tuple(output_paths),
            mandatory_output_hashes=tuple(output_hashes),
        ),
    )
    cell_path = (
        root
        / "provenance"
        / "dependencies"
        / f"cell-{execution_role.value}-{method_artifact_stem(method_name)}-seed-{seed}.json"
    )
    write_atomic_json(cell_path, cast(YamlNode, cell.model_dump(mode="json")), staging)
    return cell_path


def evaluate_emhi_seed_cell_with_retry(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    execution_role: ExecutionRole,
    method_name: MethodName,
    seed: SeedValue,
    score_path: Path,
    rank_path: Path,
    fit_path: Path,
) -> Path:
    return with_technical_retry(
        loaded,
        lambda: _evaluate_emhi_seed_cell(
            loaded,
            repository,
            experiment_name,
            execution_role,
            method_name,
            seed,
            score_path,
            rank_path,
            fit_path,
        ),
    )


def evaluate_comparator_seed_cell_with_retry(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    execution_role: ExecutionRole,
    method_name: MethodName,
    seed: SeedValue,
    score_path: Path,
    rank_path: Path,
) -> Path:
    return with_technical_retry(
        loaded,
        lambda: _evaluate_comparator_seed_cell(
            loaded,
            repository,
            experiment_name,
            execution_role,
            method_name,
            seed,
            score_path,
            rank_path,
        ),
    )


def execute_real_emhi_methods(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> tuple[RecordCount, tuple[MethodName, ...]]:
    contract = experiment_contract(loaded.values, experiment_name)
    dataset_name = campaign_dataset(loaded, experiment_name)
    supported = tuple(
        method for method in contract.methods if emhi_method_specification(method) is not None
    )
    missing = tuple(
        method for method in contract.methods if emhi_method_specification(method) is None
    )
    completed: RecordCount = 0
    _inventory_path, prepared_path, _split_path, _partitions_path, _campaigns_path = (
        preprocessing_paths(loaded, repository, dataset_name)
    )
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    if not prepared.selected_client_ids:
        return _materialize_not_tested_real_cells(loaded, repository, experiment_name, contract), ()
    for role in contract.execution_roles:
        for seed in role_seeds(loaded, role):
            completed += _execute_real_emhi_seed(
                loaded,
                repository,
                experiment_name,
                dataset_name,
                role,
                seed,
                supported,
                missing,
            )
    return completed, ()


def _materialize_not_tested_real_cells(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    contract: ExperimentContract,
) -> RecordCount:
    completed: RecordCount = 0
    for role in contract.execution_roles:
        for seed in role_seeds(loaded, role):
            for method_name in contract.methods:
                materialize_not_tested_real_cell(
                    loaded, repository, experiment_name, role, method_name, seed
                )
                completed += 1
    return completed


def _execute_real_emhi_seed(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    dataset_name: DatasetName,
    role: ExecutionRole,
    seed: SeedValue,
    supported: tuple[MethodName, ...],
    missing: tuple[MethodName, ...],
) -> RecordCount:
    seed_started = perf_counter()
    campaigns_logger().info(
        "seed_started experiment=%s role=%s dataset=%s seed=%s",
        experiment_name.value,
        role.value,
        dataset_name.value,
        seed,
    )
    score_path = materialize_detector_scores_with_retry(loaded, repository, dataset_name, seed)
    rank_path = materialize_marginal_ranks_with_retry(
        loaded, repository, dataset_name, seed, score_path
    )
    completed: RecordCount = 0
    for method_name in supported:
        fit_path = materialize_emhi_fit_with_retry(
            loaded, repository, dataset_name, seed, method_name, score_path, rank_path
        )
        evaluate_emhi_seed_cell_with_retry(
            loaded,
            repository,
            experiment_name,
            role,
            method_name,
            seed,
            score_path,
            rank_path,
            fit_path,
        )
        completed += 1
        campaigns_logger().info(
            "method_cell_completed experiment=%s role=%s seed=%s method=%s",
            experiment_name.value,
            role.value,
            seed,
            method_name.value,
        )
    for method_name in missing:
        evaluate_comparator_seed_cell_with_retry(
            loaded, repository, experiment_name, role, method_name, seed, score_path, rank_path
        )
        completed += 1
        campaigns_logger().info(
            "method_cell_completed experiment=%s role=%s seed=%s method=%s",
            experiment_name.value,
            role.value,
            seed,
            method_name.value,
        )
    campaigns_logger().info(
        "seed_completed experiment=%s role=%s seed=%s elapsed_seconds=%.3f",
        experiment_name.value,
        role.value,
        seed,
        perf_counter() - seed_started,
    )
    return completed


def sensitivity_base_specification(
    loaded: LoadedScientificConfiguration,
) -> tuple[ContextMethodName, CoalitionOrder, Boolean]:
    specification = emhi_method_specification(MethodName.FULL_FEDCAMPAIGN_EMHI)
    if specification is None:
        raise ValueError("Full FedCampaign-EMHI must be a registered EMHI hierarchy")
    return (
        specification.context_method,
        specification.maximum_order,
        specification.purification_enabled,
    )


def _sensitivity_condition_fit(
    loaded: LoadedScientificConfiguration,
    scores: DetectorScoreArtifactRecord,
    ranks: MarginalRankArtifactRecord,
    split: DatasetSplitRecord,
    context_method: ContextMethodName,
    maximum_order: CoalitionOrder,
    basis_size: BasisSize,
    cell_count: CellCount,
    purification_enabled: Boolean,
    forced_no_abstention: Boolean,
    ridge_candidates: tuple[RidgePenalty, ...] | None,
) -> EMHIFitArtifactRecord:
    condition_digest = payload_digest(
        cast(
            YamlNode,
            {
                "context_method": context_method.value,
                "basis_size": basis_size,
                "cell_count": cell_count,
                "forced_no_abstention": forced_no_abstention,
                "ridge_candidates": None if ridge_candidates is None else list(ridge_candidates),
            },
        )
    )
    fingerprint = material_fingerprint(
        nuisance_context_boundary_digest(loaded.values),
        (condition_digest,),
    )
    return build_emhi_fit_artifact(
        loaded.values,
        scores,
        ranks,
        split,
        MethodName.FULL_FEDCAMPAIGN_EMHI,
        context_method,
        maximum_order,
        basis_size,
        cell_count,
        purification_enabled,
        forced_no_abstention,
        fingerprint,
        ridge_candidates,
    )


def _emhi_metrics_for_fit(
    loaded: LoadedScientificConfiguration,
    scores: DetectorScoreArtifactRecord,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    split: DatasetSplitRecord,
    partitions: BenignPartitionRecord,
    campaigns: CampaignRegistryRecord,
    target_local_pfa: FalseAlarmRate,
) -> ContextEstimatorSensitivityMetrics:
    calibration = calibrate_operating_points(
        loaded.values,
        scores,
        ranks,
        fit,
        split.nuisance_fit_epochs,
        partitions,
        target_local_pfa,
    )
    campaign_rows, odi_values = build_campaign_rows(
        loaded, scores, ranks, fit, campaigns, calibration
    )
    rows = tuple(cast(Mapping[str, YamlNode], row) for row in campaign_rows)
    detection_rate = (
        sum(cast(int, row["global_detected_within_horizon"]) for row in rows) / len(rows)
        if rows
        else 0.0
    )
    strict_odi_rate = sum(odi_values) / len(odi_values) if odi_values else 0.0
    leads = tuple(
        cast(OperationalLeadEpochs, row["operational_lead_epochs"])
        for row in rows
        if row["operational_lead_epochs"] is not None
    )
    operational_lead_mean = sum(leads) / len(leads) if leads else None
    coverages = tuple(cast(ContextCoverage, row["context_coverage"]) for row in rows)
    context_coverage = sum(coverages) / len(coverages) if coverages else 0.0
    total_cells = sum(len(coalition_fit.cells) for coalition_fit in fit.coalition_fits)
    failed_cells = sum(
        1
        for coalition_fit in fit.coalition_fits
        for cell in coalition_fit.cells
        if cell.numerical_failure
    )
    return ContextEstimatorSensitivityMetrics(
        heldout_pfa=calibration.global_operating_point.heldout_upper_pfa,
        campaign_detection_rate=detection_rate,
        strict_odi_rate=strict_odi_rate,
        operational_lead_mean=operational_lead_mean,
        context_coverage=context_coverage,
        abstention_rate=1.0 - context_coverage,
        numerical_failure_rate=(failed_cells / total_cells if total_cells else 0.0),
    )


def sensitivity_conditions(
    loaded: LoadedScientificConfiguration,
    base_context_method: ContextMethodName,
) -> tuple[
    tuple[
        BasisSize | None,
        CellCount | None,
        RidgePenalty | None,
        ContextMethodName | None,
        BasisSize,
        CellCount,
        tuple[RidgePenalty, ...] | None,
        ContextMethodName,
        Boolean,
    ],
    ...,
]:
    sensitivity = loaded.values.experiments.context_and_estimator_sensitivity
    primary_basis_size = loaded.values.basis.primary_size
    primary_cell_count = loaded.values.context.primary_cell_count
    conditions: list[
        tuple[
            BasisSize | None,
            CellCount | None,
            RidgePenalty | None,
            ContextMethodName | None,
            BasisSize,
            CellCount,
            tuple[RidgePenalty, ...] | None,
            ContextMethodName,
            Boolean,
        ]
    ] = []
    for basis_size in loaded.values.basis.sensitivity_sizes:
        conditions.append(
            (
                basis_size,
                None,
                None,
                None,
                basis_size,
                primary_cell_count,
                None,
                base_context_method,
                False,
            )
        )
    for cell_count in loaded.values.context.cell_count_sensitivity:
        conditions.append(
            (
                None,
                cell_count,
                None,
                None,
                primary_basis_size,
                cell_count,
                None,
                base_context_method,
                False,
            )
        )
    conditions.append(
        (
            None,
            None,
            sensitivity.forced_ridge,
            None,
            primary_basis_size,
            primary_cell_count,
            (sensitivity.forced_ridge,),
            base_context_method,
            False,
        )
    )
    for context_variant in sensitivity.context_variants:
        forced_no_abstention = context_variant is ContextMethodName.FORCED_NO_ABSTENTION
        variant_context_method = base_context_method if forced_no_abstention else context_variant
        conditions.append(
            (
                None,
                None,
                None,
                context_variant,
                primary_basis_size,
                primary_cell_count,
                None,
                variant_context_method,
                forced_no_abstention,
            )
        )
    return tuple(conditions)


def sensitivity_cell_slug(
    basis_override: BasisSize | None,
    cell_override: CellCount | None,
    ridge_override: RidgePenalty | None,
    method_override: ContextMethodName | None,
) -> RelativePath:
    if basis_override is not None:
        return f"basis-size-{basis_override}"
    if cell_override is not None:
        return f"context-cell-count-{cell_override}"
    if ridge_override is not None:
        return f"forced-ridge-{ridge_override}"
    if method_override is not None:
        return method_override.value.lower().replace(" ", "-")
    raise ValueError("sensitivity cell requires exactly one overridden factor")


def materialize_context_and_estimator_sensitivity_cells(
    loaded: LoadedScientificConfiguration,
    repository: Path,
) -> tuple[Path, ...]:
    experiment_name = ExperimentName.CONTEXT_AND_ESTIMATOR_SENSITIVITY
    dataset_name = loaded.values.datasets.primary.name
    base_context_method, maximum_order, purification_enabled = sensitivity_base_specification(
        loaded
    )
    _inventory_path, prepared_path, split_path, partitions_path, campaigns_path = (
        preprocessing_paths(loaded, repository, dataset_name)
    )
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    if not prepared.selected_client_ids:
        return ()
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    partitions = BenignPartitionRecord.model_validate_json(partitions_path.read_bytes())
    campaigns = CampaignRegistryRecord.model_validate_json(campaigns_path.read_bytes())
    target_local_pfa = local_pfa_target(loaded, experiment_name)
    conditions = sensitivity_conditions(loaded, base_context_method)
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    staging = layout.roots.outputs_root / "cache" / "staging"
    paths: list[Path] = []
    for seed in loaded.values.randomness.real_development_roots:
        score_path = materialize_detector_scores_with_retry(loaded, repository, dataset_name, seed)
        rank_path = materialize_marginal_ranks_with_retry(
            loaded, repository, dataset_name, seed, score_path
        )
        base_fit_path = materialize_emhi_fit_with_retry(
            loaded,
            repository,
            dataset_name,
            seed,
            MethodName.FULL_FEDCAMPAIGN_EMHI,
            score_path,
            rank_path,
        )
        scores = DetectorScoreArtifactRecord.model_validate_json(score_path.read_bytes())
        ranks = MarginalRankArtifactRecord.model_validate_json(rank_path.read_bytes())
        base_fit = EMHIFitArtifactRecord.model_validate_json(base_fit_path.read_bytes())
        base_metrics = _emhi_metrics_for_fit(
            loaded, scores, ranks, base_fit, split, partitions, campaigns, target_local_pfa
        )
        for (
            basis_override,
            cell_override,
            ridge_override,
            method_override,
            basis_size,
            cell_count,
            ridge_candidates,
            context_method,
            forced_no_abstention,
        ) in conditions:
            condition_fit = _sensitivity_condition_fit(
                loaded,
                scores,
                ranks,
                split,
                context_method,
                maximum_order,
                basis_size,
                cell_count,
                purification_enabled,
                forced_no_abstention,
                ridge_candidates,
            )
            condition_metrics = _emhi_metrics_for_fit(
                loaded, scores, ranks, condition_fit, split, partitions, campaigns, target_local_pfa
            )
            source_paths = (score_path, rank_path, base_fit_path)
            source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
            payload: YamlNode = {
                "seed": seed,
                "basis_size_override": basis_override,
                "context_cell_count_override": cell_override,
                "forced_ridge_override": ridge_override,
                "context_method_override": (
                    None if method_override is None else method_override.value
                ),
                "condition": cast(YamlNode, condition_metrics.model_dump(mode="json")),
                "base": cast(YamlNode, base_metrics.model_dump(mode="json")),
                "source_result_ids": list(source_ids),
            }
            record = ContextEstimatorSensitivityCellRecord(
                seed=seed,
                basis_size_override=basis_override,
                context_cell_count_override=cell_override,
                forced_ridge_override=ridge_override,
                context_method_override=method_override,
                condition=condition_metrics,
                base=base_metrics,
                source_result_ids=source_ids,
                dependency_fingerprint=material_fingerprint(
                    nuisance_context_boundary_digest(loaded.values),
                    tuple(file_sha256(path) for path in source_paths),
                ),
                content_digest=payload_digest(payload),
            )
            slug = sensitivity_cell_slug(
                basis_override, cell_override, ridge_override, method_override
            )
            path = root / "diagnostics" / "sensitivity" / f"seed-{seed}" / f"{slug}.json"
            write_atomic_json(path, cast(YamlNode, record.model_dump(mode="json")), staging)
            paths.append(path)
    return tuple(paths)
