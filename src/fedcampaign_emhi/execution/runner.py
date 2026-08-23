from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import cast

from fedcampaign_emhi.artifacts.paths import build_artifact_layout
from fedcampaign_emhi.artifacts.provenance import material_fingerprint
from fedcampaign_emhi.artifacts.records import (
    ArtifactManifest,
    ClientDetectorScoreStream,
    ClientMarginalRankStream,
    CoalitionFitRecord,
    CompletionRecord,
    ConditionalRankReferenceRecord,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
    EMHIFitArtifactRecord,
    ExperimentRunRecord,
    MarginalRankArtifactRecord,
    OrderContextFitRecord,
    PlanArtifactRecord,
    PlannedExperimentRecord,
    PreparedDatasetRecord,
    ProjectionCellFitRecord,
    ScientificCellRecord,
)
from fedcampaign_emhi.artifacts.storage import file_sha256, payload_digest, write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.detection.detector_assignment import assign_detector_families
from fedcampaign_emhi.detection.fitting import (
    score_autoencoder,
    score_isolation_forest,
    score_one_class_svm,
)
from fedcampaign_emhi.detection.scoring import rank_stream, score_stream_isolation_check
from fedcampaign_emhi.domain.enums import (
    ArtifactLifecycleState,
    ArtifactNamespace,
    ClaimState,
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
    DetectorFamily,
    ExecutionRole,
    ExperimentName,
    ExperimentState,
    MethodName,
    OverwritePolicy,
    PreprocessingLayer,
)
from fedcampaign_emhi.domain.types import (
    ArtifactIdentity,
    BinIndex,
    ClientId,
    CoalitionMembers,
    ComponentName,
    ContextTrainingRow,
    EpochIndexValue,
    FiniteFloat,
    MaterialDependencyFingerprint,
    RankReference,
    RankValue,
    RecordCount,
    ResumeStep,
    RuntimeSeconds,
    SeedDerivationIdentity,
    SeedValue,
)
from fedcampaign_emhi.emhi.basis import tensor_representation
from fedcampaign_emhi.emhi.coalitions import enumerate_coalitions
from fedcampaign_emhi.emhi.contexts import (
    assign_context_cell,
    cap_context_training_rows,
    context_cluster_identity,
    exact_exclusion_members,
    fit_context_centroids,
    minimum_support_epochs_for_order,
    outside_context_histogram,
)
from fedcampaign_emhi.emhi.evidence import operational_norm_reference_quantile
from fedcampaign_emhi.emhi.innovation_calibration import calibrate_innovations_on_nuisance_fit
from fedcampaign_emhi.emhi.projection import proper_subset_design_row
from fedcampaign_emhi.emhi.ranks import coalition_conditioned_residual_rank
from fedcampaign_emhi.evaluation.smoke_gate import run_synthetic_module_validation
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE, plan_experiments
from fedcampaign_emhi.execution.preprocess import dataset_directory_stem, layer_artifact_id
from fedcampaign_emhi.experiments.definitions import ExperimentContract, experiment_registry
from fedcampaign_emhi.experiments.validation import assert_known_experiment
from fedcampaign_emhi.runtime.determinism import derive_component_seed
from fedcampaign_emhi.synthetic.validation import validate_synthetic_generators


@dataclass(frozen=True)
class ExperimentExecutionResult:
    experiment_name: ExperimentName
    state: ExperimentState
    run_record_path: Path
    completed_cell_count: RecordCount
    detail: ComponentName


def resume_sequence() -> tuple[ResumeStep, ...]:
    return RESUME_SEQUENCE


def validate_scientific_implementation_registry(
    config: ScientificConfig, experiment_name: ExperimentName
) -> None:
    assert_known_experiment(config, experiment_name)
    contract = _experiment_contract(config, experiment_name)
    real_without_explicit_methods = {
        ExperimentName.CONTEXT_AND_ESTIMATOR_SENSITIVITY,
        ExperimentName.COALITION_SCALABILITY,
    }
    if (
        contract.uses_real_seeds
        and not contract.methods
        and experiment_name not in real_without_explicit_methods
    ):
        raise ValueError(f"real-data experiment {experiment_name.value} has no configured methods")


def _experiment_contract(
    config: ScientificConfig, experiment_name: ExperimentName
) -> ExperimentContract:
    return next(
        contract
        for contract in experiment_registry(config)
        if contract.experiment_name is experiment_name
    )


def _run_record_path(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> Path:
    layout = build_artifact_layout(loaded, repository)
    return (
        layout.experiment_outputs_root(experiment_name)
        / "provenance"
        / "dependencies"
        / "run-record.json"
    )


def publish_experiment_run_record(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    overwrite_policy: OverwritePolicy,
    state: ExperimentState,
) -> Path:
    if state in {ExperimentState.NOT_STARTED, ExperimentState.READY}:
        raise ValueError("run records require an active, blocked, or terminal execution state")
    layout = build_artifact_layout(loaded, repository)
    staging = layout.roots.outputs_root / "cache" / "staging"
    destination = _run_record_path(loaded, repository, experiment_name)
    record = ExperimentRunRecord(
        experiment_name=experiment_name,
        material_digest=loaded.material_digest,
        overwrite_policy=overwrite_policy,
        resume_sequence=RESUME_SEQUENCE,
        state=state,
    )
    write_atomic_json(destination, cast(YamlNode, record.model_dump(mode="json")), staging)
    return destination


def _existing_completed_run(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    overwrite_policy: OverwritePolicy,
) -> ExperimentExecutionResult | None:
    if overwrite_policy is OverwritePolicy.OVERWRITE:
        return None
    path = _run_record_path(loaded, repository, experiment_name)
    if not path.is_file():
        return None
    try:
        record = ExperimentRunRecord.model_validate_json(path.read_bytes())
    except ValueError:
        return None
    if (
        record.material_digest != loaded.material_digest
        or record.state is not ExperimentState.COMPLETED
    ):
        return None
    completed_cells = tuple(child for child in path.parent.glob("cell-*.json") if child.is_file())
    if not completed_cells:
        return None
    return ExperimentExecutionResult(
        experiment_name=experiment_name,
        state=ExperimentState.COMPLETED,
        run_record_path=path,
        completed_cell_count=len(completed_cells),
        detail="reused compatible completed experiment",
    )


def _execute_synthetic_module_validation(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    overwrite_policy: OverwritePolicy,
) -> ExperimentExecutionResult:
    experiment_name = ExperimentName.SYNTHETIC_MODULE_VALIDATION
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    staging = layout.roots.outputs_root / "cache" / "staging"
    started = perf_counter()
    invariant_gate = run_synthetic_module_validation(loaded)
    generator_gate = validate_synthetic_generators(loaded)
    state = (
        ExperimentState.COMPLETED
        if invariant_gate.passed and generator_gate.state is ExperimentState.COMPLETED
        else ExperimentState.INVALID
    )
    diagnostic_path = root / "diagnostics" / "scientific" / "synthetic-validation.json"
    diagnostic_payload: YamlNode = {
        "state": state.value,
        "invariant_failures": [failure.label for failure in invariant_gate.failures],
        "generator_failures": list(generator_gate.failed_checks),
    }
    diagnostic_hash = write_atomic_json(diagnostic_path, diagnostic_payload, staging)
    dependency_fingerprint = material_fingerprint(loaded.material_digest, ())
    completion = CompletionRecord(
        state=state,
        mandatory_output_paths=(diagnostic_path.relative_to(repository).as_posix(),),
        mandatory_output_hashes=(diagnostic_hash,),
    )
    elapsed: RuntimeSeconds = perf_counter() - started
    cell = ScientificCellRecord(
        experiment_name=experiment_name,
        execution_role=ExecutionRole.VALIDATION,
        semantic_cell_path="validation/synthetic-module-validation",
        method_name=None,
        seed=None,
        state=state,
        material_digest=loaded.material_digest,
        selected_client_ids=(),
        upstream_artifact_ids=(),
        dependency_fingerprint=dependency_fingerprint,
        runtime_seconds=elapsed,
        peak_rss_bytes=0,
        application_payload_bytes=len(diagnostic_path.read_bytes()),
        completion_record=completion,
    )
    cell_path = root / "provenance" / "dependencies" / "cell-validation.json"
    write_atomic_json(cell_path, cast(YamlNode, cell.model_dump(mode="json")), staging)
    run_path = publish_experiment_run_record(
        loaded, repository, experiment_name, overwrite_policy, state
    )
    return ExperimentExecutionResult(
        experiment_name=experiment_name,
        state=state,
        run_record_path=run_path,
        completed_cell_count=1 if state is ExperimentState.COMPLETED else 0,
        detail="synthetic scientific invariants and generator contracts executed",
    )


def _experiment_dataset(
    loaded: LoadedScientificConfiguration, experiment_name: ExperimentName
) -> DatasetName:
    if experiment_name is ExperimentName.SECONDARY_CONTROLLED_TRACE_GENERALIZATION:
        return loaded.values.datasets.secondary.name
    return loaded.values.datasets.primary.name


def _preprocessing_paths(
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


def _required_preprocessing_artifacts(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> tuple[Path, ...]:
    contract = _experiment_contract(loaded.values, experiment_name)
    if not contract.uses_real_seeds:
        return ()
    return _preprocessing_paths(loaded, repository, _experiment_dataset(loaded, experiment_name))


def _required_real_roots(
    loaded: LoadedScientificConfiguration, experiment_name: ExperimentName
) -> tuple[SeedValue, ...]:
    contract = _experiment_contract(loaded.values, experiment_name)
    roots: list[SeedValue] = []
    if not contract.uses_real_seeds:
        return ()
    for role in contract.execution_roles:
        if role is ExecutionRole.CONFIRMATORY:
            roots.extend(loaded.values.randomness.real_confirmatory_roots)
        else:
            roots.extend(loaded.values.randomness.real_development_roots)
    return tuple(dict.fromkeys(roots))


def _score_artifact_id(dataset_name: DatasetName, root_seed: SeedValue) -> ArtifactIdentity:
    return f"detector-scores.{dataset_directory_stem(dataset_name)}.seed-{root_seed}"


def _score_artifact_path(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
) -> Path:
    layout = build_artifact_layout(loaded, repository)
    return (
        layout.roots.outputs_root
        / "artifacts"
        / "scores"
        / dataset_directory_stem(dataset_name)
        / f"seed-{root_seed}.json"
    )


def _detector_dependency_fingerprint(
    loaded: LoadedScientificConfiguration,
    prepared_path: Path,
    split_path: Path,
    root_seed: SeedValue,
) -> MaterialDependencyFingerprint:
    detector_config_digest = payload_digest(
        cast(YamlNode, loaded.values.detectors.model_dump(mode="json"))
    )
    seed_digest = payload_digest(cast(YamlNode, {"root_seed": root_seed}))
    return material_fingerprint(
        detector_config_digest,
        (file_sha256(prepared_path), file_sha256(split_path), seed_digest),
    )


def _detector_seed(
    root_seed: SeedValue, dataset_name: DatasetName, client_id: ClientId
) -> SeedValue:
    return derive_component_seed(
        SeedDerivationIdentity(
            base_seed=root_seed,
            component_name="local-detector-fit",
            dataset=dataset_name,
            client_ids=(client_id,),
            coalition_ids=(),
            condition_coordinates=(),
        )
    )


def _score_client(
    loaded: LoadedScientificConfiguration,
    detector_family: DetectorFamily,
    fit_rows: tuple[tuple[FiniteFloat, ...], ...],
    score_rows: tuple[tuple[FiniteFloat, ...], ...],
    detector_seed: SeedValue,
    client_id: ClientId,
) -> tuple[FiniteFloat, ...]:
    if detector_family is DetectorFamily.ISOLATION_FOREST:
        config = loaded.values.detectors.isolation_forest
        return score_isolation_forest(
            fit_rows,
            score_rows,
            config.trees,
            config.max_samples_cap,
            config.max_features,
            config.jobs,
            detector_seed,
        )
    if detector_family is DetectorFamily.ONE_CLASS_SVM:
        config = loaded.values.detectors.one_class_svm
        return score_one_class_svm(
            fit_rows,
            score_rows,
            config.nu,
            config.coefficient_zero,
            config.solver_tolerance,
            config.kernel_cache_mib,
            config.max_iterations,
            detector_seed,
        )
    config = loaded.values.detectors.autoencoder
    if len(config.betas) != 2:
        raise ValueError("autoencoder requires exactly two Adam beta coefficients")
    return score_autoencoder(
        fit_rows,
        score_rows,
        config.learning_rate,
        config.betas[0],
        config.betas[1],
        config.optimizer_epsilon,
        config.weight_decay,
        config.batch_size,
        config.epochs,
        detector_seed,
        client_id,
    )


def _write_manifest(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    destination: Path,
    artifact_id: ArtifactIdentity,
    content_digest: str,
    fingerprint: MaterialDependencyFingerprint,
    upstream_ids: tuple[ArtifactIdentity, ...],
) -> None:
    layout = build_artifact_layout(loaded, repository)
    staging = layout.roots.outputs_root / "cache" / "staging"
    manifest = ArtifactManifest(
        artifact_id=artifact_id,
        namespace=ArtifactNamespace.OUTPUTS,
        experiment_name=None,
        relative_path=destination.relative_to(layout.roots.outputs_root).as_posix(),
        content_digest=content_digest,
        material_fingerprint=fingerprint,
        upstream_ids=upstream_ids,
        lifecycle_state=ArtifactLifecycleState.VALID,
    )
    write_atomic_json(
        destination.with_suffix(".manifest.json"),
        cast(YamlNode, manifest.model_dump(mode="json")),
        staging,
    )


def _materialize_detector_scores(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
) -> Path:
    _, prepared_path, split_path, _, _ = _preprocessing_paths(loaded, repository, dataset_name)
    fingerprint = _detector_dependency_fingerprint(loaded, prepared_path, split_path, root_seed)
    destination = _score_artifact_path(loaded, repository, dataset_name, root_seed)
    if destination.is_file():
        try:
            existing = DetectorScoreArtifactRecord.model_validate_json(destination.read_bytes())
        except ValueError:
            existing = None
        if existing is not None and existing.dependency_fingerprint == fingerprint:
            return destination
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    assignments = assign_detector_families(split.selected_client_ids)
    streams: list[ClientDetectorScoreStream] = []
    for assignment in assignments:
        client_rows = tuple(row for row in prepared.epochs if row.client_id == assignment.client_id)
        fit_rows = tuple(
            row.feature_values for row in client_rows if row.epoch_index in split.detector_fit_epochs
        )
        if not fit_rows:
            raise ValueError(
                f"selected client {assignment.client_id} has no benign detector-fit rows"
            )
        score_rows = tuple(row.feature_values for row in client_rows)
        detector_seed = _detector_seed(root_seed, dataset_name, assignment.client_id)
        scores = _score_client(
            loaded,
            assignment.family,
            fit_rows,
            score_rows,
            detector_seed,
            assignment.client_id,
        )
        score_stream_isolation_check(len(scores), len(client_rows))
        streams.append(
            ClientDetectorScoreStream(
                client_id=assignment.client_id,
                detector_family=assignment.family,
                detector_seed=detector_seed,
                epoch_indexes=tuple(row.epoch_index for row in client_rows),
                scores=scores,
            )
        )
    record = DetectorScoreArtifactRecord(
        dataset_name=dataset_name,
        root_seed=root_seed,
        selected_client_ids=split.selected_client_ids,
        client_streams=tuple(streams),
        dependency_fingerprint=fingerprint,
    )
    layout = build_artifact_layout(loaded, repository)
    staging = layout.roots.outputs_root / "cache" / "staging"
    content_digest = write_atomic_json(
        destination, cast(YamlNode, record.model_dump(mode="json")), staging
    )
    _write_manifest(
        loaded,
        repository,
        destination,
        _score_artifact_id(dataset_name, root_seed),
        content_digest,
        fingerprint,
        (
            layer_artifact_id(dataset_name, PreprocessingLayer.PREPARED),
            layer_artifact_id(dataset_name, PreprocessingLayer.SPLITS),
        ),
    )
    return destination


def _rank_artifact_id(dataset_name: DatasetName, root_seed: SeedValue) -> ArtifactIdentity:
    return f"marginal-ranks.{dataset_directory_stem(dataset_name)}.seed-{root_seed}"


def _rank_artifact_path(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
) -> Path:
    layout = build_artifact_layout(loaded, repository)
    return (
        layout.roots.outputs_root
        / "artifacts"
        / "fitted"
        / dataset_directory_stem(dataset_name)
        / f"seed-{root_seed}-marginal-ranks.json"
    )


def _materialize_marginal_ranks(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
    score_path: Path,
) -> Path:
    _, _, split_path, _, _ = _preprocessing_paths(loaded, repository, dataset_name)
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    scores = DetectorScoreArtifactRecord.model_validate_json(score_path.read_bytes())
    rank_config_digest = payload_digest(
        cast(YamlNode, {"rank_clip_epsilon": loaded.values.context.rank_clip_epsilon})
    )
    fingerprint = material_fingerprint(
        rank_config_digest,
        (file_sha256(score_path), file_sha256(split_path)),
    )
    destination = _rank_artifact_path(loaded, repository, dataset_name, root_seed)
    if destination.is_file():
        try:
            existing = MarginalRankArtifactRecord.model_validate_json(destination.read_bytes())
        except ValueError:
            existing = None
        if existing is not None and existing.dependency_fingerprint == fingerprint:
            return destination
    streams: list[ClientMarginalRankStream] = []
    nuisance_epochs = set(split.nuisance_fit_epochs)
    for score_stream in scores.client_streams:
        reference_scores = tuple(
            score
            for epoch, score in zip(score_stream.epoch_indexes, score_stream.scores, strict=True)
            if epoch in nuisance_epochs
        )
        ranks = rank_stream(
            score_stream.scores,
            reference_scores,
            loaded.values.context.rank_clip_epsilon,
        )
        streams.append(
            ClientMarginalRankStream(
                client_id=score_stream.client_id,
                nuisance_reference_scores=reference_scores,
                epoch_indexes=score_stream.epoch_indexes,
                ranks=ranks,
            )
        )
    record = MarginalRankArtifactRecord(
        dataset_name=dataset_name,
        root_seed=root_seed,
        selected_client_ids=scores.selected_client_ids,
        client_streams=tuple(streams),
        dependency_fingerprint=fingerprint,
    )
    layout = build_artifact_layout(loaded, repository)
    staging = layout.roots.outputs_root / "cache" / "staging"
    content_digest = write_atomic_json(
        destination, cast(YamlNode, record.model_dump(mode="json")), staging
    )
    _write_manifest(
        loaded,
        repository,
        destination,
        _rank_artifact_id(dataset_name, root_seed),
        content_digest,
        fingerprint,
        (
            _score_artifact_id(dataset_name, root_seed),
            layer_artifact_id(dataset_name, PreprocessingLayer.SPLITS),
        ),
    )
    return destination


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


def _context_seed(
    loaded: LoadedScientificConfiguration,
    dataset_name: DatasetName,
    root_seed: SeedValue,
    coalition_order: CoalitionOrder,
) -> SeedValue:
    return derive_component_seed(
        SeedDerivationIdentity(
            base_seed=loaded.values.randomness.context_base_seed,
            component_name=f"exact-exclusion-context-order-{int(coalition_order)}-root-{root_seed}",
            dataset=dataset_name,
            client_ids=(),
            coalition_ids=(),
            condition_coordinates=(),
        )
    )


def _coalition_context_row(
    loaded: LoadedScientificConfiguration,
    ranks: MarginalRankArtifactRecord,
    coalition: CoalitionMembers,
    epoch_index: EpochIndexValue,
) -> ContextTrainingRow | None:
    lagged_epoch = epoch_index - loaded.values.context.outside_lag_epochs
    complement = exact_exclusion_members(ranks.selected_client_ids, coalition.client_ids)
    lagged_ranks: list[tuple[ClientId, RankValue]] = []
    available_clients: list[ClientId] = []
    for client_id in complement:
        rank = _rank_at_epoch(ranks, client_id, lagged_epoch)
        if rank is None:
            continue
        lagged_ranks.append((client_id, rank))
        available_clients.append(client_id)
    histogram = outside_context_histogram(
        tuple(lagged_ranks),
        tuple(available_clients),
        complement,
        loaded.values.context.outside_histogram_bin_count,
        loaded.values.context.minimum_available_outside_clients,
        loaded.values.context.minimum_available_outside_fraction,
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


def _minimum_support(
    loaded: LoadedScientificConfiguration, coalition_order: CoalitionOrder
) -> RecordCount:
    minimum = loaded.values.context.minimum_support_epochs
    return minimum_support_epochs_for_order(
        coalition_order,
        minimum.order_one,
        minimum.order_two,
        minimum.order_three,
    )


def _fit_order_context(
    loaded: LoadedScientificConfiguration,
    ranks: MarginalRankArtifactRecord,
    coalitions: tuple[CoalitionMembers, ...],
    nuisance_epochs: tuple[EpochIndexValue, ...],
    coalition_order: CoalitionOrder,
) -> OrderContextFitRecord:
    rows = tuple(
        row
        for coalition in coalitions
        if coalition.order is coalition_order
        for epoch_index in nuisance_epochs
        for row in (_coalition_context_row(loaded, ranks, coalition, epoch_index),)
        if row is not None
    )
    context_seed = _context_seed(loaded, ranks.dataset_name, ranks.root_seed, coalition_order)
    capped = cap_context_training_rows(
        rows,
        context_seed,
        loaded.values.context.kmeans.max_fit_rows,
    )
    identity = context_cluster_identity(
        ranks.dataset_name,
        coalition_order,
        ContextMethodName.EXACT_COALITION_EXCLUSION,
        ranks.root_seed,
    )
    centroids = fit_context_centroids(
        capped,
        identity,
        loaded.values.context.primary_cell_count,
        loaded.values.context.kmeans.n_init,
        loaded.values.context.kmeans.max_iterations,
        loaded.values.context.kmeans.tolerance,
        loaded.values.context.kmeans.assignment_tie_tolerance,
        context_seed,
    )
    if centroids is None:
        return OrderContextFitRecord(
            coalition_order=coalition_order,
            context_method=ContextMethodName.EXACT_COALITION_EXCLUSION,
            centroids=(),
            state=ClaimState.NOT_TESTED,
        )
    return OrderContextFitRecord(
        coalition_order=coalition_order,
        context_method=ContextMethodName.EXACT_COALITION_EXCLUSION,
        centroids=centroids.centroids,
        state=ClaimState.SUPPORTED,
    )


def _coalition_cell_epochs(
    loaded: LoadedScientificConfiguration,
    ranks: MarginalRankArtifactRecord,
    coalition: CoalitionMembers,
    nuisance_epochs: tuple[EpochIndexValue, ...],
    centroids: tuple[tuple[FiniteFloat, ...], ...],
    context_cell: BinIndex,
) -> tuple[EpochIndexValue, ...]:
    selected: list[EpochIndexValue] = []
    for epoch_index in nuisance_epochs:
        row = _coalition_context_row(loaded, ranks, coalition, epoch_index)
        if row is None:
            continue
        assigned = assign_context_cell(
            row.histogram,
            centroids,
            loaded.values.context.kmeans.assignment_tie_tolerance,
        )
        if assigned == context_cell:
            selected.append(epoch_index)
    return tuple(selected)


def _conditional_rank_reference(
    ranks: MarginalRankArtifactRecord,
    client_id: ClientId,
    context_cell: BinIndex,
    epochs: tuple[EpochIndexValue, ...],
) -> ConditionalRankReferenceRecord:
    reference = tuple(
        rank
        for epoch_index in epochs
        for rank in (_rank_at_epoch(ranks, client_id, epoch_index),)
        if rank is not None
    )
    return ConditionalRankReferenceRecord(
        client_id=client_id,
        context_cell=context_cell,
        reference_ranks=reference,
    )


def _conditioned_member_ranks(
    loaded: LoadedScientificConfiguration,
    ranks: MarginalRankArtifactRecord,
    coalition: CoalitionMembers,
    epoch_index: EpochIndexValue,
    references: tuple[ConditionalRankReferenceRecord, ...],
) -> tuple[RankValue, ...] | None:
    conditioned: list[RankValue] = []
    for client_id in coalition.client_ids:
        marginal = _rank_at_epoch(ranks, client_id, epoch_index)
        reference_record = next(
            (reference for reference in references if reference.client_id == client_id),
            None,
        )
        if marginal is None or reference_record is None or not reference_record.reference_ranks:
            return None
        conditioned.append(
            coalition_conditioned_residual_rank(
                marginal,
                RankReference(scores=reference_record.reference_ranks),
                loaded.values.context.rank_clip_epsilon,
            )
        )
    return tuple(conditioned)


def _fit_projection_cell(
    loaded: LoadedScientificConfiguration,
    ranks: MarginalRankArtifactRecord,
    coalition: CoalitionMembers,
    context_cell: BinIndex,
    epochs: tuple[EpochIndexValue, ...],
) -> ProjectionCellFitRecord:
    references = tuple(
        _conditional_rank_reference(ranks, client_id, context_cell, epochs)
        for client_id in coalition.client_ids
    )
    if len(epochs) < _minimum_support(loaded, coalition.order):
        return ProjectionCellFitRecord(
            context_cell=context_cell,
            conditional_rank_references=references,
            selected_ridge_penalty=None,
            complete_nuisance_coefficients=(),
            coordinate_means=(),
            coordinate_deviations=(),
            operational_norm_reference=None,
            state=ClaimState.NOT_TESTED,
        )
    conditioned_rows = tuple(
        conditioned
        for epoch_index in epochs
        for conditioned in (
            _conditioned_member_ranks(loaded, ranks, coalition, epoch_index, references),
        )
        if conditioned is not None
    )
    design_rows = tuple(
        proper_subset_design_row(row, loaded.values.basis.primary_size) for row in conditioned_rows
    )
    tensors = tuple(
        tensor_representation(row, loaded.values.basis.primary_size) for row in conditioned_rows
    )
    calibration = calibrate_innovations_on_nuisance_fit(
        design_rows,
        tensors,
        loaded.values.projection.ridge_candidates,
        loaded.values.context.nuisance_crossfit.fold_count,
        loaded.values.projection.selection_tie_tolerance_mse,
        loaded.values.projection.zero_ridge_svd_relative_cutoff,
        loaded.values.projection.atom_scale_floor,
    )
    if calibration is None:
        return ProjectionCellFitRecord(
            context_cell=context_cell,
            conditional_rank_references=references,
            selected_ridge_penalty=None,
            complete_nuisance_coefficients=(),
            coordinate_means=(),
            coordinate_deviations=(),
            operational_norm_reference=None,
            state=ClaimState.NOT_TESTED,
        )
    norm_reference = operational_norm_reference_quantile(
        calibration.standardized_held_fold_innovations,
        loaded.values.evidence.operational_norm_reference_quantile,
    )
    return ProjectionCellFitRecord(
        context_cell=context_cell,
        conditional_rank_references=references,
        selected_ridge_penalty=calibration.selected_ridge_penalty,
        complete_nuisance_coefficients=calibration.complete_nuisance_coefficients,
        coordinate_means=calibration.coordinate_means,
        coordinate_deviations=calibration.coordinate_deviations,
        operational_norm_reference=norm_reference,
        state=ClaimState.SUPPORTED,
    )


def _fit_coalition(
    loaded: LoadedScientificConfiguration,
    ranks: MarginalRankArtifactRecord,
    coalition: CoalitionMembers,
    nuisance_epochs: tuple[EpochIndexValue, ...],
    order_context: OrderContextFitRecord,
) -> CoalitionFitRecord:
    if order_context.state is not ClaimState.SUPPORTED:
        return CoalitionFitRecord(
            coalition_client_ids=coalition.client_ids,
            coalition_order=coalition.order,
            cells=(),
            state=ClaimState.NOT_TESTED,
        )
    cells = tuple(
        _fit_projection_cell(
            loaded,
            ranks,
            coalition,
            context_cell,
            _coalition_cell_epochs(
                loaded,
                ranks,
                coalition,
                nuisance_epochs,
                order_context.centroids,
                context_cell,
            ),
        )
        for context_cell in range(len(order_context.centroids))
    )
    state = (
        ClaimState.SUPPORTED
        if any(cell.state is ClaimState.SUPPORTED for cell in cells)
        else ClaimState.NOT_TESTED
    )
    return CoalitionFitRecord(
        coalition_client_ids=coalition.client_ids,
        coalition_order=coalition.order,
        cells=cells,
        state=state,
    )


def _emhi_fit_artifact_id(dataset_name: DatasetName, root_seed: SeedValue) -> ArtifactIdentity:
    return f"full-emhi-fit.{dataset_directory_stem(dataset_name)}.seed-{root_seed}"


def _emhi_fit_path(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
) -> Path:
    layout = build_artifact_layout(loaded, repository)
    return (
        layout.roots.outputs_root
        / "artifacts"
        / "fitted"
        / dataset_directory_stem(dataset_name)
        / f"seed-{root_seed}-full-emhi.json"
    )


def _materialize_full_emhi_fit(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
    rank_path: Path,
) -> Path:
    _, _, split_path, _, _ = _preprocessing_paths(loaded, repository, dataset_name)
    fit_config_digest = payload_digest(
        cast(
            YamlNode,
            {
                "context": loaded.values.context.model_dump(mode="json"),
                "basis": loaded.values.basis.model_dump(mode="json"),
                "projection": loaded.values.projection.model_dump(mode="json"),
                "evidence": {
                    "operational_norm_reference_quantile": loaded.values.evidence.operational_norm_reference_quantile
                },
                "maximum_coalition_order": loaded.values.study.maximum_coalition_order,
            },
        )
    )
    fingerprint = material_fingerprint(
        fit_config_digest,
        (file_sha256(rank_path), file_sha256(split_path)),
    )
    destination = _emhi_fit_path(loaded, repository, dataset_name, root_seed)
    if destination.is_file():
        try:
            existing = EMHIFitArtifactRecord.model_validate_json(destination.read_bytes())
        except ValueError:
            existing = None
        if existing is not None and existing.dependency_fingerprint == fingerprint:
            return destination
    ranks = MarginalRankArtifactRecord.model_validate_json(rank_path.read_bytes())
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    maximum_order = CoalitionOrder(int(loaded.values.study.maximum_coalition_order))
    coalitions = enumerate_coalitions(split.selected_client_ids, maximum_order)
    order_contexts = tuple(
        _fit_order_context(
            loaded,
            ranks,
            coalitions,
            split.nuisance_fit_epochs,
            coalition_order,
        )
        for coalition_order in CoalitionOrder
        if coalition_order <= maximum_order
    )
    coalition_fits = tuple(
        _fit_coalition(
            loaded,
            ranks,
            coalition,
            split.nuisance_fit_epochs,
            next(context for context in order_contexts if context.coalition_order is coalition.order),
        )
        for coalition in coalitions
    )
    record = EMHIFitArtifactRecord(
        dataset_name=dataset_name,
        root_seed=root_seed,
        method_name=MethodName.FULL_FEDCAMPAIGN_EMHI,
        selected_client_ids=split.selected_client_ids,
        order_contexts=order_contexts,
        coalition_fits=coalition_fits,
        dependency_fingerprint=fingerprint,
    )
    layout = build_artifact_layout(loaded, repository)
    staging = layout.roots.outputs_root / "cache" / "staging"
    content_digest = write_atomic_json(
        destination, cast(YamlNode, record.model_dump(mode="json")), staging
    )
    _write_manifest(
        loaded,
        repository,
        destination,
        _emhi_fit_artifact_id(dataset_name, root_seed),
        content_digest,
        fingerprint,
        (
            _rank_artifact_id(dataset_name, root_seed),
            layer_artifact_id(dataset_name, PreprocessingLayer.SPLITS),
        ),
    )
    return destination


def _materialize_real_prerequisites(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> tuple[Path, ...]:
    dataset_name = _experiment_dataset(loaded, experiment_name)
    roots = _required_real_roots(loaded, experiment_name)
    produced: list[Path] = []
    for root_seed in roots:
        score_path = _materialize_detector_scores(loaded, repository, dataset_name, root_seed)
        rank_path = _materialize_marginal_ranks(
            loaded, repository, dataset_name, root_seed, score_path
        )
        fit_path = _materialize_full_emhi_fit(
            loaded, repository, dataset_name, root_seed, rank_path
        )
        produced.extend((score_path, rank_path, fit_path))
    return tuple(produced)


def execute_experiment(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    overwrite_policy: OverwritePolicy,
) -> ExperimentExecutionResult:
    validate_scientific_implementation_registry(loaded.values, experiment_name)
    reused = _existing_completed_run(loaded, repository, experiment_name, overwrite_policy)
    if reused is not None:
        return reused
    if experiment_name is ExperimentName.SYNTHETIC_MODULE_VALIDATION:
        return _execute_synthetic_module_validation(loaded, repository, overwrite_policy)
    contract = _experiment_contract(loaded.values, experiment_name)
    if contract.uses_synthetic_seeds and not contract.uses_real_seeds:
        run_path = publish_experiment_run_record(
            loaded,
            repository,
            experiment_name,
            overwrite_policy,
            ExperimentState.BLOCKED,
        )
        return ExperimentExecutionResult(
            experiment_name=experiment_name,
            state=ExperimentState.BLOCKED,
            run_record_path=run_path,
            completed_cell_count=0,
            detail="synthetic experiment producer remains to be executed",
        )
    required = _required_preprocessing_artifacts(loaded, repository, experiment_name)
    missing = tuple(path for path in required if not path.is_file())
    if missing:
        run_path = publish_experiment_run_record(
            loaded,
            repository,
            experiment_name,
            overwrite_policy,
            ExperimentState.BLOCKED,
        )
        return ExperimentExecutionResult(
            experiment_name=experiment_name,
            state=ExperimentState.BLOCKED,
            run_record_path=run_path,
            completed_cell_count=0,
            detail="required canonical preprocessing artifacts are missing",
        )
    produced = _materialize_real_prerequisites(loaded, repository, experiment_name)
    run_path = publish_experiment_run_record(
        loaded,
        repository,
        experiment_name,
        overwrite_policy,
        ExperimentState.BLOCKED,
    )
    return ExperimentExecutionResult(
        experiment_name=experiment_name,
        state=ExperimentState.BLOCKED,
        run_record_path=run_path,
        completed_cell_count=0,
        detail=f"materialized {len(produced)} reusable detector, rank, and EMHI fit artifacts; evaluation remains",
    )


def publish_plan_artifact(loaded: LoadedScientificConfiguration, repository: Path) -> Path:
    layout = build_artifact_layout(loaded, repository)
    staging = layout.roots.outputs_root / "cache" / "staging"
    destination = layout.roots.outputs_root / "preprocessing" / "metadata" / "execution-plan.json"
    record = PlanArtifactRecord(
        material_digest=loaded.material_digest,
        resume_sequence=RESUME_SEQUENCE,
        experiments=tuple(
            PlannedExperimentRecord(
                experiment_name=planned.experiment_name,
                execution_role=planned.execution_role,
                seed_count=planned.seed_count,
                state=planned.state,
            )
            for planned in plan_experiments(loaded)
        ),
    )
    write_atomic_json(destination, cast(YamlNode, record.model_dump(mode="json")), staging)
    return destination
