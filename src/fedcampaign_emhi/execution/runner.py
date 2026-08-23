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
    CompletionRecord,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
    ExperimentRunRecord,
    MarginalRankArtifactRecord,
    PlanArtifactRecord,
    PlannedExperimentRecord,
    PreparedDatasetRecord,
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
    DatasetName,
    DetectorFamily,
    ExecutionRole,
    ExperimentName,
    ExperimentState,
    GroundTruthClass,
    OverwritePolicy,
)
from fedcampaign_emhi.domain.types import (
    ArtifactIdentity,
    ClientId,
    ComponentName,
    FiniteFloat,
    MaterialDependencyFingerprint,
    RecordCount,
    ResumeStep,
    RuntimeSeconds,
    SeedDerivationIdentity,
    SeedValue,
)
from fedcampaign_emhi.evaluation.smoke_gate import run_synthetic_module_validation
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE, plan_experiments
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
    if contract.uses_real_seeds and not contract.methods and experiment_name not in {
        ExperimentName.CONTEXT_AND_ESTIMATOR_SENSITIVITY,
        ExperimentName.COALITION_SCALABILITY,
    }:
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
    record = ExperimentRunRecord.model_validate_json(path.read_bytes())
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
        mandatory_output_paths=(str(diagnostic_path.relative_to(repository)),),
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
    stem = dataset_name.value.replace(" ", "_")
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
    return _preprocessing_paths(
        loaded, repository, _experiment_dataset(loaded, experiment_name)
    )


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


def _dataset_stem(dataset_name: DatasetName) -> str:
    return dataset_name.value.replace(" ", "_")


def _score_artifact_id(dataset_name: DatasetName, root_seed: SeedValue) -> ArtifactIdentity:
    return f"detector-scores.{_dataset_stem(dataset_name)}.seed-{root_seed}"


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
        / _dataset_stem(dataset_name)
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


def _materialize_detector_scores(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
) -> Path:
    _, prepared_path, split_path, _, _ = _preprocessing_paths(
        loaded, repository, dataset_name
    )
    fingerprint = _detector_dependency_fingerprint(
        loaded, prepared_path, split_path, root_seed
    )
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
        client_rows = tuple(
            row
            for row in prepared.epochs
            if row.client_id == assignment.client_id
            and row.ground_truth is not GroundTruthClass.AMBIGUOUS
        )
        fit_rows = tuple(
            row.feature_values
            for row in client_rows
            if row.epoch_index in split.detector_fit_epochs
            and row.ground_truth is GroundTruthClass.BENIGN
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
    manifest = ArtifactManifest(
        artifact_id=_score_artifact_id(dataset_name, root_seed),
        namespace=ArtifactNamespace.OUTPUTS,
        experiment_name=None,
        relative_path=destination.relative_to(layout.roots.outputs_root).as_posix(),
        content_digest=content_digest,
        material_fingerprint=fingerprint,
        upstream_ids=(
            f"preprocess.{_dataset_stem(dataset_name)}.prepared",
            f"preprocess.{_dataset_stem(dataset_name)}.splits",
        ),
        lifecycle_state=ArtifactLifecycleState.VALID,
    )
    write_atomic_json(
        destination.with_suffix(".manifest.json"),
        cast(YamlNode, manifest.model_dump(mode="json")),
        staging,
    )
    return destination


def _rank_artifact_id(dataset_name: DatasetName, root_seed: SeedValue) -> ArtifactIdentity:
    return f"marginal-ranks.{_dataset_stem(dataset_name)}.seed-{root_seed}"


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
        / _dataset_stem(dataset_name)
        / f"seed-{root_seed}-marginal-ranks.json"
    )


def _rank_dependency_fingerprint(
    loaded: LoadedScientificConfiguration,
    score_path: Path,
    split_path: Path,
) -> MaterialDependencyFingerprint:
    rank_config_digest = payload_digest(
        cast(
            YamlNode,
            {"rank_clip_epsilon": loaded.values.context.rank_clip_epsilon},
        )
    )
    return material_fingerprint(
        rank_config_digest,
        (file_sha256(score_path), file_sha256(split_path)),
    )


def _materialize_marginal_ranks(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
    score_path: Path,
) -> Path:
    _, _, split_path, _, _ = _preprocessing_paths(loaded, repository, dataset_name)
    fingerprint = _rank_dependency_fingerprint(loaded, score_path, split_path)
    destination = _rank_artifact_path(loaded, repository, dataset_name, root_seed)
    if destination.is_file():
        try:
            existing = MarginalRankArtifactRecord.model_validate_json(destination.read_bytes())
        except ValueError:
            existing = None
        if existing is not None and existing.dependency_fingerprint == fingerprint:
            return destination
    scores = DetectorScoreArtifactRecord.model_validate_json(score_path.read_bytes())
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    streams: list[ClientMarginalRankStream] = []
    for client_stream in scores.client_streams:
        nuisance_reference_scores = tuple(
            score
            for epoch_index, score in zip(
                client_stream.epoch_indexes, client_stream.scores, strict=True
            )
            if epoch_index in split.nuisance_fit_epochs
        )
        ranks = rank_stream(
            client_stream.scores,
            nuisance_reference_scores,
            loaded.values.context.rank_clip_epsilon,
        )
        streams.append(
            ClientMarginalRankStream(
                client_id=client_stream.client_id,
                nuisance_reference_scores=nuisance_reference_scores,
                epoch_indexes=client_stream.epoch_indexes,
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
    manifest = ArtifactManifest(
        artifact_id=_rank_artifact_id(dataset_name, root_seed),
        namespace=ArtifactNamespace.OUTPUTS,
        experiment_name=None,
        relative_path=destination.relative_to(layout.roots.outputs_root).as_posix(),
        content_digest=content_digest,
        material_fingerprint=fingerprint,
        upstream_ids=(_score_artifact_id(dataset_name, root_seed),),
        lifecycle_state=ArtifactLifecycleState.VALID,
    )
    write_atomic_json(
        destination.with_suffix(".manifest.json"),
        cast(YamlNode, manifest.model_dump(mode="json")),
        staging,
    )
    return destination


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
    missing = tuple(
        path
        for path in _required_preprocessing_artifacts(loaded, repository, experiment_name)
        if not path.is_file()
    )
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
    dataset_name = _experiment_dataset(loaded, experiment_name)
    roots = _required_real_roots(loaded, experiment_name)
    score_paths = tuple(
        _materialize_detector_scores(loaded, repository, dataset_name, root_seed)
        for root_seed in roots
    )
    rank_paths = tuple(
        _materialize_marginal_ranks(
            loaded, repository, dataset_name, root_seed, score_path
        )
        for root_seed, score_path in zip(roots, score_paths, strict=True)
    )
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
        detail=(
            f"materialized {len(score_paths)} detector score streams and "
            f"{len(rank_paths)} nuisance-fit marginal-rank artifacts; EMHI fit remains"
        ),
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
    write_atomic_json(
        destination, cast(YamlNode, record.model_dump(mode="json")), staging
    )
    return destination
