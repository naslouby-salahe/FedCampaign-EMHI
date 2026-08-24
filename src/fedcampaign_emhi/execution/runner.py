import hashlib
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import cast

from fedcampaign_emhi.analysis.multiplicity import holm_adjusted_p_values
from fedcampaign_emhi.analysis.statistics import (
    exact_sign_flip_means,
    paired_mean_bca_interval,
    two_sided_sign_flip_p_value,
)
from fedcampaign_emhi.analysis.summaries import build_seed_summary
from fedcampaign_emhi.artifacts.paths import build_artifact_layout
from fedcampaign_emhi.artifacts.provenance import material_fingerprint
from fedcampaign_emhi.artifacts.records import (
    ArtifactManifest,
    BenignPartitionRecord,
    CampaignRegistryRecord,
    CompletionRecord,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
    EMHIFitArtifactRecord,
    ExperimentRunRecord,
    MarginalRankArtifactRecord,
    PlanArtifactRecord,
    PlannedExperimentRecord,
    PreparedDatasetRecord,
    ScientificCellRecord,
    SeedSummaryRecord,
    StatisticalRecord,
)
from fedcampaign_emhi.artifacts.storage import file_sha256, payload_digest, write_atomic_json
from fedcampaign_emhi.comparators.composition import (
    materialize_composition_record,
    select_strongest_comparator,
)
from fedcampaign_emhi.comparators.contracts import (
    ComparatorMethodContract,
    comparator_method_contracts,
)
from fedcampaign_emhi.comparators.runtime import (
    score_comparator_ranks,
    validate_comparator_runtime_contracts,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.detection.scoring import build_detector_score_artifact
from fedcampaign_emhi.domain.enums import (
    ArtifactLifecycleState,
    ArtifactNamespace,
    ClaimState,
    CoalitionOrder,
    ContextMethodName,
    DatasetName,
    ExecutionRole,
    ExperimentName,
    ExperimentState,
    MethodName,
    OverwritePolicy,
    PartitionRole,
    PreprocessingLayer,
)
from fedcampaign_emhi.domain.types import (
    ArtifactIdentity,
    ComponentName,
    ConfigurationDigest,
    EpochIndexValue,
    FalseAlarmRate,
    FiniteFloat,
    MaterialDependencyFingerprint,
    OdiIndicator,
    RankValue,
    RecordCount,
    RelativePath,
    ResumeStep,
    RuntimeSeconds,
    SeedValue,
)
from fedcampaign_emhi.emhi.innovation_calibration import build_emhi_fit_artifact
from fedcampaign_emhi.emhi.ranks import build_marginal_rank_artifact
from fedcampaign_emhi.evaluation.benign_horizons import (
    calibrate_operating_points,
    heldout_benign_false_stop_records,
)
from fedcampaign_emhi.evaluation.campaign_replay import (
    campaign_trajectory,
    global_stop_epoch,
    local_stop_epochs,
    operational_lead,
    statistical_lead,
    trajectory_context_coverage,
)
from fedcampaign_emhi.evaluation.metrics import decisive_order, earliest_local_stop
from fedcampaign_emhi.evaluation.records import (
    OperationalCalibration,
    SequentialTrajectory,
    odi_evaluation_record,
)
from fedcampaign_emhi.evaluation.smoke_gate import run_synthetic_module_validation
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE, plan_experiments
from fedcampaign_emhi.execution.preprocess import dataset_directory_stem, layer_artifact_id
from fedcampaign_emhi.experiments.definitions import ExperimentContract, experiment_registry
from fedcampaign_emhi.experiments.producers import (
    SyntheticCellOutcome,
    run_synthetic_cell,
    synthetic_role_seeds,
)
from fedcampaign_emhi.experiments.validation import assert_known_experiment
from fedcampaign_emhi.synthetic.validation import validate_synthetic_generators


@dataclass(frozen=True)
class ExperimentExecutionResult:
    experiment_name: ExperimentName
    state: ExperimentState
    run_record_path: Path
    completed_cell_count: RecordCount
    detail: ComponentName


@dataclass(frozen=True)
class _EmhiMethodSpecification:
    method_name: MethodName
    context_method: ContextMethodName
    maximum_order: CoalitionOrder
    purification_enabled: bool


def resume_sequence() -> tuple[ResumeStep, ...]:
    return RESUME_SEQUENCE


def _experiment_contract(
    config: ScientificConfig, experiment_name: ExperimentName
) -> ExperimentContract:
    return next(
        contract
        for contract in experiment_registry(config)
        if contract.experiment_name is experiment_name
    )


def validate_scientific_implementation_registry(
    config: ScientificConfig, experiment_name: ExperimentName
) -> None:
    validate_comparator_runtime_contracts(config)
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


def _method_contract(method_name: MethodName) -> ComparatorMethodContract | None:
    return next(
        (
            contract
            for contract in comparator_method_contracts()
            if contract.method_name is method_name
        ),
        None,
    )


def _emhi_method_specification(method_name: MethodName) -> _EmhiMethodSpecification | None:
    contract = _method_contract(method_name)
    if contract is None or contract.context_method is None or contract.enabled_order_set is None:
        return None
    if contract.is_equivalence_comparator:
        return None
    purification = contract.proper_subset_purification_enabled
    if purification is None:
        return None
    return _EmhiMethodSpecification(
        method_name=method_name,
        context_method=contract.context_method,
        maximum_order=max(contract.enabled_order_set),
        purification_enabled=purification,
    )


def _method_slug(method_name: MethodName) -> RelativePath:
    return method_name.value.lower().replace(" ", "-").replace("≤", "at-most-").replace("_", "-")


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


def _implementation_digest(repository: Path) -> ConfigurationDigest:
    source_root = repository / "src" / "fedcampaign_emhi"
    digest = hashlib.sha256()
    for source_path in sorted(source_root.rglob("*.py")):
        digest.update(source_path.relative_to(source_root).as_posix().encode("utf-8"))
        digest.update(source_path.read_bytes())
    return digest.hexdigest()


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
        implementation_digest=_implementation_digest(repository),
        overwrite_policy=overwrite_policy,
        resume_sequence=RESUME_SEQUENCE,
        state=state,
    )
    write_atomic_json(destination, cast(YamlNode, record.model_dump(mode="json")), staging)
    return destination


def _completed_cell_is_reusable(
    repository: Path, path: Path, material_digest: ConfigurationDigest
) -> bool:
    try:
        cell = ScientificCellRecord.model_validate_json(path.read_bytes())
    except ValueError:
        return False
    if cell.state is not ExperimentState.COMPLETED or cell.material_digest != material_digest:
        return False
    outputs = cell.completion_record.mandatory_output_paths
    hashes = cell.completion_record.mandatory_output_hashes
    if len(outputs) != len(hashes):
        return False
    for relative_path, expected_hash in zip(outputs, hashes, strict=True):
        absolute = repository / relative_path
        if not absolute.is_file() or file_sha256(absolute) != expected_hash:
            return False
    return True


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
        or record.implementation_digest != _implementation_digest(repository)
        or record.state is not ExperimentState.COMPLETED
    ):
        return None
    cell_paths = tuple(sorted(path.parent.glob("cell-*.json")))
    if not cell_paths or not all(
        _completed_cell_is_reusable(repository, cell_path, loaded.material_digest)
        for cell_path in cell_paths
    ):
        return None
    return ExperimentExecutionResult(
        experiment_name=experiment_name,
        state=ExperimentState.COMPLETED,
        run_record_path=path,
        completed_cell_count=len(cell_paths),
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
    fingerprint = material_fingerprint(loaded.material_digest, ())
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
        dependency_fingerprint=fingerprint,
        runtime_seconds=elapsed,
        peak_rss_bytes=0,
        application_payload_bytes=len(diagnostic_path.read_bytes()),
        completion_record=completion,
    )
    cell_path = root / "provenance" / "dependencies" / "cell-validation.json"
    write_atomic_json(cell_path, cast(YamlNode, cell.model_dump(mode="json")), staging)
    run_path = publish_experiment_run_record(
        loaded,
        repository,
        experiment_name,
        overwrite_policy,
        state,
    )
    return ExperimentExecutionResult(
        experiment_name=experiment_name,
        state=state,
        run_record_path=run_path,
        completed_cell_count=1 if state is ExperimentState.COMPLETED else 0,
        detail="synthetic scientific invariants and generator contracts executed",
    )


def _execute_synthetic_experiment(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    overwrite_policy: OverwritePolicy,
) -> ExperimentExecutionResult:
    contract = _experiment_contract(loaded.values, experiment_name)
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    staging = layout.roots.outputs_root / "cache" / "staging"
    if experiment_name is ExperimentName.STRONG_COMPARATOR_COMPOSITION_CHALLENGE:
        selection = loaded.values.experiments.strong_comparator_composition_challenge
        candidate_scores: list[FiniteFloat] = []
        for method_name in selection.candidates:
            outcome = run_synthetic_cell(
                loaded,
                experiment_name,
                loaded.values.randomness.synthetic_development_roots[0],
                method_name,
            )
            candidate_scores.append(
                abs(
                    (outcome.method_score or 0.0)
                    - loaded.values.generators.pure_polynomial.primary_reference_theta
                )
            )
        selected_method = select_strongest_comparator(
            selection.candidates,
            tuple(candidate_scores),
            tuple(0.0 for _candidate in selection.candidates),
            selection.error_tie_tolerance_standardized_units,
            selection.runtime_tie_tolerance_seconds,
        )
        composition = materialize_composition_record(
            selected_method,
            selection.artifact_filename,
        )
        composition_path = root / "artifacts" / "derived" / selection.artifact_filename
        write_atomic_json(
            composition_path,
            {
                "selected_method": composition.selected_method.value,
                "native_target_order": composition.native_target_order,
                "artifact_filename": composition.artifact_filename,
            },
            staging,
        )
    completed = 0
    invalid = 0
    for role in contract.execution_roles:
        methods: tuple[MethodName | None, ...] = contract.methods or (None,)
        for seed in synthetic_role_seeds(loaded, role):
            for method_name in methods:
                started = perf_counter()
                try:
                    outcome = run_synthetic_cell(loaded, experiment_name, seed, method_name)
                except (ArithmeticError, ValueError) as error:
                    outcome = SyntheticCellOutcome((str(error),), None)
                state = (
                    ExperimentState.COMPLETED
                    if not outcome.failed_checks
                    else ExperimentState.INVALID
                )
                method_slug = (
                    "coordinate-validation" if method_name is None else _method_slug(method_name)
                )
                diagnostic_path = (
                    root
                    / "diagnostics"
                    / "scientific"
                    / role.value
                    / method_slug
                    / f"seed-{seed}.json"
                )
                diagnostic_payload: YamlNode = {
                    "experiment_name": experiment_name.value,
                    "execution_role": role.value,
                    "seed": seed,
                    "method_name": None if method_name is None else method_name.value,
                    "state": state.value,
                    "failed_checks": list(outcome.failed_checks),
                    "method_score": outcome.method_score,
                    "evidence": outcome.evidence,
                }
                diagnostic_hash = write_atomic_json(diagnostic_path, diagnostic_payload, staging)
                fingerprint = material_fingerprint(
                    loaded.material_digest,
                    (payload_digest(cast(YamlNode, {"seed": seed, "method": method_slug})),),
                )
                completion = CompletionRecord(
                    state=state,
                    mandatory_output_paths=(diagnostic_path.relative_to(repository).as_posix(),),
                    mandatory_output_hashes=(diagnostic_hash,),
                )
                cell = ScientificCellRecord(
                    experiment_name=experiment_name,
                    execution_role=role,
                    semantic_cell_path=f"{role.value}/{method_slug}/seed-{seed}",
                    method_name=method_name,
                    seed=seed,
                    state=state,
                    material_digest=loaded.material_digest,
                    selected_client_ids=(),
                    upstream_artifact_ids=(),
                    dependency_fingerprint=fingerprint,
                    runtime_seconds=perf_counter() - started,
                    peak_rss_bytes=0,
                    application_payload_bytes=len(diagnostic_path.read_bytes()),
                    completion_record=completion,
                )
                cell_path = (
                    root
                    / "provenance"
                    / "dependencies"
                    / f"cell-{role.value}-{method_slug}-seed-{seed}.json"
                )
                write_atomic_json(cell_path, cast(YamlNode, cell.model_dump(mode="json")), staging)
                if state is ExperimentState.COMPLETED:
                    completed += 1
                else:
                    invalid += 1
    state = ExperimentState.COMPLETED if invalid == 0 else ExperimentState.INVALID
    run_path = publish_experiment_run_record(
        loaded,
        repository,
        experiment_name,
        overwrite_policy,
        state,
    )
    return ExperimentExecutionResult(
        experiment_name=experiment_name,
        state=state,
        run_record_path=run_path,
        completed_cell_count=completed,
        detail=(
            "synthetic producer cells executed"
            if invalid == 0
            else f"{invalid} synthetic cells failed scientific validation"
        ),
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


def _score_artifact_id(dataset_name: DatasetName, root_seed: SeedValue) -> ArtifactIdentity:
    return f"detector-scores.{dataset_directory_stem(dataset_name)}.seed-{root_seed}"


def _rank_artifact_id(dataset_name: DatasetName, root_seed: SeedValue) -> ArtifactIdentity:
    return f"marginal-ranks.{dataset_directory_stem(dataset_name)}.seed-{root_seed}"


def _fit_artifact_id(
    dataset_name: DatasetName,
    root_seed: SeedValue,
    method_name: MethodName,
) -> ArtifactIdentity:
    return (
        f"emhi-fit.{dataset_directory_stem(dataset_name)}."
        f"seed-{root_seed}.{_method_slug(method_name)}"
    )


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


def _fit_artifact_path(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
    method_name: MethodName,
) -> Path:
    layout = build_artifact_layout(loaded, repository)
    return (
        layout.roots.outputs_root
        / "artifacts"
        / "fitted"
        / dataset_directory_stem(dataset_name)
        / f"seed-{root_seed}"
        / f"{_method_slug(method_name)}.json"
    )


def _write_manifest(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    destination: Path,
    artifact_id: ArtifactIdentity,
    content_digest: ConfigurationDigest,
    fingerprint: MaterialDependencyFingerprint,
    upstream_ids: tuple[ArtifactIdentity, ...],
) -> None:
    layout = build_artifact_layout(loaded, repository)
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
        layout.roots.outputs_root / "cache" / "staging",
    )


def _materialize_detector_scores(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    root_seed: SeedValue,
) -> Path:
    _inventory_path, prepared_path, split_path, _partitions_path, _campaigns_path = (
        _preprocessing_paths(loaded, repository, dataset_name)
    )
    detector_digest = payload_digest(
        cast(YamlNode, loaded.values.detectors.model_dump(mode="json"))
    )
    seed_digest = payload_digest(cast(YamlNode, {"root_seed": root_seed}))
    fingerprint = material_fingerprint(
        detector_digest,
        (file_sha256(prepared_path), file_sha256(split_path), seed_digest),
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
    _write_manifest(
        loaded,
        repository,
        destination,
        _score_artifact_id(dataset_name, root_seed),
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
        _preprocessing_paths(loaded, repository, dataset_name)
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
    destination = _rank_artifact_path(loaded, repository, dataset_name, root_seed)
    if destination.is_file():
        try:
            existing = MarginalRankArtifactRecord.model_validate_json(destination.read_bytes())
        except ValueError:
            existing = None
        if existing is not None and existing.dependency_fingerprint == fingerprint:
            return destination
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
    _write_manifest(
        loaded,
        repository,
        destination,
        _rank_artifact_id(dataset_name, root_seed),
        content_hash,
        fingerprint,
        (
            _score_artifact_id(dataset_name, root_seed),
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
    specification = _emhi_method_specification(method_name)
    if specification is None:
        raise ValueError(f"method {method_name.value} is not an EMHI hierarchy")
    _inventory_path, _prepared_path, split_path, _partitions_path, _campaigns_path = (
        _preprocessing_paths(loaded, repository, dataset_name)
    )
    method_digest = payload_digest(
        cast(
            YamlNode,
            {
                "method_name": method_name.value,
                "context_method": specification.context_method.value,
                "maximum_order": int(specification.maximum_order),
                "basis_size": loaded.values.basis.primary_size,
                "cell_count": loaded.values.context.primary_cell_count,
                "purification_enabled": specification.purification_enabled,
            },
        )
    )
    fingerprint = material_fingerprint(
        loaded.material_digest,
        (
            method_digest,
            file_sha256(score_path),
            file_sha256(rank_path),
            file_sha256(split_path),
        ),
    )
    destination = _fit_artifact_path(
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
            return destination
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
    _write_manifest(
        loaded,
        repository,
        destination,
        _fit_artifact_id(dataset_name, root_seed, method_name),
        content_hash,
        fingerprint,
        (
            _score_artifact_id(dataset_name, root_seed),
            _rank_artifact_id(dataset_name, root_seed),
            layer_artifact_id(dataset_name, PreprocessingLayer.SPLITS),
        ),
    )
    return destination


def _local_pfa_target(
    loaded: LoadedScientificConfiguration,
    experiment_name: ExperimentName,
) -> FalseAlarmRate:
    if experiment_name is ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE:
        return loaded.values.local_policy.strong_horizon_pfa_target
    return loaded.values.local_policy.primary_horizon_pfa_target


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


def _campaign_rows(
    loaded: LoadedScientificConfiguration,
    scores: DetectorScoreArtifactRecord,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    campaigns: CampaignRegistryRecord,
    calibration: OperationalCalibration,
) -> tuple[tuple[YamlNode, ...], tuple[FiniteFloat, ...]]:
    rows: list[YamlNode] = []
    odi_values: list[FiniteFloat] = []
    threshold = calibration.global_operating_point.threshold
    for campaign in campaigns.campaigns:
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
        indicator: OdiIndicator = odi.indicator
        odi_values.append(float(indicator))
        rows.append(
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
                "decisive_order": None if decisive is None else int(decisive),
                "context_coverage": coverage,
                "abstention_rate": 1.0 - coverage,
                "server_latency_seconds": elapsed,
                "end_to_end_latency_seconds": elapsed,
            }
        )
    return tuple(rows), tuple(odi_values)


def _heldout_rows(
    loaded: LoadedScientificConfiguration,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    partitions: BenignPartitionRecord,
    calibration: OperationalCalibration,
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
        _preprocessing_paths(loaded, repository, _experiment_dataset(loaded, experiment_name))
    )
    target_local_pfa = _local_pfa_target(loaded, experiment_name)
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
        loaded.material_digest,
        (method_digest, *(file_sha256(path) for path in required_paths)),
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
    )
    campaign_rows, odi_values = _campaign_rows(
        loaded,
        scores,
        ranks,
        fit,
        campaigns,
        calibration,
    )
    heldout_rows = _heldout_rows(loaded, ranks, fit, partitions, calibration)
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    staging = layout.roots.outputs_root / "cache" / "staging"
    method_slug = _method_slug(method_name)
    evaluation_id = _evaluation_artifact_id(
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
        "calibration": _calibration_payload(calibration),
        PartitionRole.HELDOUT_BENIGN.value: list(heldout_rows),
        "campaigns": list(campaign_rows),
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
        _score_artifact_id(dataset_name, seed),
        _rank_artifact_id(dataset_name, seed),
        _fit_artifact_id(dataset_name, seed, method_name),
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
    return cell_path


def _role_seeds(
    loaded: LoadedScientificConfiguration,
    role: ExecutionRole,
) -> tuple[SeedValue, ...]:
    if role is ExecutionRole.CONFIRMATORY:
        return loaded.values.randomness.real_confirmatory_roots
    return loaded.values.randomness.real_development_roots


def _materialize_not_tested_real_cell(
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
    method_slug = "coordinate-validation" if method_name is None else _method_slug(method_name)
    raw_path = (
        root / "evaluations" / "raw" / execution_role.value / method_slug / f"seed-{seed}.json"
    )
    fingerprint = material_fingerprint(
        loaded.material_digest,
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
        "claim_state": "NOT_TESTED",
        "reason": "no eligible raw records were available after canonical preprocessing",
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


def _comparator_scoring_method(
    loaded: LoadedScientificConfiguration, method_name: MethodName
) -> MethodName:
    if method_name is MethodName.SELECTED_STRONG_COMPARATOR_COMPOSITION:
        return loaded.values.experiments.strong_comparator_composition_challenge.candidates[0]
    return method_name


def _comparator_epoch_scores(
    loaded: LoadedScientificConfiguration,
    ranks: MarginalRankArtifactRecord,
    method_name: MethodName,
) -> tuple[tuple[EpochIndexValue, FiniteFloat], ...]:
    streams = tuple(
        (
            stream.client_id,
            tuple(zip(stream.epoch_indexes, stream.ranks, strict=True)),
        )
        for stream in ranks.client_streams
    )
    if not streams:
        return ()
    epoch_sets: tuple[set[EpochIndexValue], ...] = tuple(
        {epoch for epoch, _rank in stream} for _client_id, stream in streams
    )
    common_epoch_set: set[EpochIndexValue] = set(epoch_sets[0])
    for epoch_set in epoch_sets[1:]:
        common_epoch_set.intersection_update(epoch_set)
    common_epochs: list[EpochIndexValue] = sorted(common_epoch_set)
    scoring_method = _comparator_scoring_method(loaded, method_name)
    triple_methods = {
        MethodName.CONDITIONAL_PAIR_DEPENDENCE,
        MethodName.EXCLUSION_MATCHED_LANCASTER_TRIPLE,
        MethodName.CONNECTED_INFORMATION_REFERENCE,
        MethodName.D_VINE_CONDITIONAL_REFERENCE,
        MethodName.CONDITIONAL_LOG_LINEAR_REFERENCE,
    }
    scores: list[tuple[EpochIndexValue, FiniteFloat]] = []
    cusum_state: tuple[FiniteFloat, ...] = ()
    for epoch in common_epochs:
        values: tuple[RankValue, ...] = tuple(
            next(rank for candidate_epoch, rank in stream if candidate_epoch == epoch)
            for _client_id, stream in streams
        )
        inputs = values[:3] if scoring_method in triple_methods else values
        score, cusum_state = score_comparator_ranks(
            scoring_method,
            inputs,
            loaded.values,
            cusum_state,
        )
        scores.append((epoch, score))
    return tuple(scores)


def _comparator_stop(
    scores: tuple[tuple[EpochIndexValue, FiniteFloat], ...],
    epochs: tuple[EpochIndexValue, ...],
    threshold: FiniteFloat | None,
) -> EpochIndexValue | None:
    if threshold is None:
        return None
    return next(
        (
            epoch
            for epoch in epochs
            if next((score for score_epoch, score in scores if score_epoch == epoch), 0.0)
            > threshold
        ),
        None,
    )


def _comparator_score_at(
    scores: tuple[tuple[EpochIndexValue, FiniteFloat], ...], epoch: EpochIndexValue
) -> FiniteFloat | None:
    return next((score for score_epoch, score in scores if score_epoch == epoch), None)


def _materialize_seed_statistics(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> tuple[Path, ...]:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    summary_paths = tuple(sorted((root / "metrics" / "seed-summaries").glob("**/*.json")))
    summaries = tuple(
        SeedSummaryRecord.model_validate_json(path.read_bytes()) for path in summary_paths
    )
    method_groups: list[tuple[MethodName, tuple[SeedSummaryRecord, ...]]] = []
    for summary in summaries:
        existing = next(
            (
                index
                for index, (method_name, _records) in enumerate(method_groups)
                if method_name is summary.method_name
            ),
            None,
        )
        if existing is None:
            method_groups.append((summary.method_name, (summary,)))
        else:
            method_name, records = method_groups[existing]
            method_groups[existing] = (method_name, (*records, summary))
    if not method_groups:
        return ()
    raw_p_values: list[FiniteFloat] = []
    estimates: list[FiniteFloat] = []
    intervals: list[tuple[FiniteFloat, FiniteFloat] | None] = []
    sources: list[tuple[ArtifactIdentity, ...]] = []
    fingerprints: list[MaterialDependencyFingerprint] = []
    for _method_name, records in method_groups:
        values = tuple(record.method_value for record in records)
        estimate = sum(values) / len(values)
        estimates.append(estimate)
        source_ids = tuple(
            source_id for record in records for source_id in record.source_evaluation_ids
        )
        sources.append(source_ids)
        hashes = tuple(record.content_digest for record in records)
        fingerprints.append(material_fingerprint(loaded.material_digest, hashes))
        if len(values) < 2:
            raw_p_values.append(1.0)
            intervals.append(None)
            continue
        flipped = exact_sign_flip_means(values)
        raw_p_values.append(two_sided_sign_flip_p_value(estimate, flipped))
        intervals.append(
            paired_mean_bca_interval(
                values,
                loaded.values.statistics.confidence_level,
                loaded.values.statistics.bootstrap_replicates,
                loaded.values.randomness.statistical_analysis_base_seed,
            )
        )
    adjusted = holm_adjusted_p_values(
        tuple(method_name.value for method_name, _records in method_groups),
        tuple(raw_p_values),
    )
    staging = layout.roots.outputs_root / "cache" / "staging"
    paths: list[Path] = []
    for index, (method_name, records) in enumerate(method_groups):
        interval = intervals[index]
        decision = (
            ClaimState.SUPPORTED
            if adjusted[index] < loaded.values.statistics.nominal_significance_alpha
            else ClaimState.NULL_RESULT
        )
        payload: YamlNode = {
            "experiment_name": experiment_name.value,
            "method_name": method_name.value,
            "metric_name": "strict_odi_rate",
            "estimate": estimates[index],
            "raw_p_value": raw_p_values[index],
            "adjusted_p_value": adjusted[index],
            "confidence_level": loaded.values.statistics.confidence_level,
            "confidence_lower": None if interval is None else interval[0],
            "confidence_upper": None if interval is None else interval[1],
            "decision": decision.value,
            "source_result_ids": list(sources[index]),
            "independent_unit_count": len(records),
        }
        record = StatisticalRecord(
            hypothesis_identifier=f"{experiment_name.value}:{method_name.value}:strict_odi_rate",
            metric_name="strict_odi_rate",
            method_name=method_name,
            independent_unit_count=len(records),
            estimate=estimates[index],
            raw_p_value=raw_p_values[index],
            adjusted_p_value=adjusted[index],
            confidence_level=loaded.values.statistics.confidence_level,
            confidence_lower=None if interval is None else interval[0],
            confidence_upper=None if interval is None else interval[1],
            decision=decision,
            source_result_ids=sources[index],
            dependency_fingerprint=fingerprints[index],
            content_digest=payload_digest(payload),
        )
        path = (
            root / "statistics" / "seed-level" / f"{_method_slug(method_name)}-strict-odi-rate.json"
        )
        write_atomic_json(path, cast(YamlNode, record.model_dump(mode="json")), staging)
        paths.append(path)
    return tuple(paths)


def _evaluate_comparator_seed_cell(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    execution_role: ExecutionRole,
    method_name: MethodName,
    seed: SeedValue,
    rank_path: Path,
) -> Path:
    dataset_name = _experiment_dataset(loaded, experiment_name)
    _inventory_path, _prepared_path, split_path, partitions_path, campaigns_path = (
        _preprocessing_paths(loaded, repository, dataset_name)
    )
    ranks = MarginalRankArtifactRecord.model_validate_json(rank_path.read_bytes())
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    partitions = BenignPartitionRecord.model_validate_json(partitions_path.read_bytes())
    campaigns = CampaignRegistryRecord.model_validate_json(campaigns_path.read_bytes())
    scores = _comparator_epoch_scores(loaded, ranks, method_name)
    calibration_values = tuple(
        score
        for epoch in split.threshold_calibration_epochs
        if (score := _comparator_score_at(scores, epoch)) is not None
    )
    threshold = None if not calibration_values else max(calibration_values)
    campaign_rows: list[YamlNode] = []
    odi_values: list[FiniteFloat] = []
    for campaign in campaigns.campaigns:
        epochs = tuple(range(campaign.start_epoch, campaign.end_epoch + 1))
        stop_epoch = _comparator_stop(scores, epochs, threshold)
        odi_values.append(0.0)
        campaign_rows.append(
            {
                "start_epoch": campaign.start_epoch,
                "end_epoch": campaign.end_epoch,
                "participating_client_ids": list(campaign.participating_client_ids),
                "global_stop_epoch": stop_epoch,
                "local_stop_epochs": [None for _client in ranks.selected_client_ids],
                "local_min_stop_epoch": None,
                "strict_odi": 0,
                "global_detected_within_horizon": int(stop_epoch is not None),
                "local_detected_within_horizon": 0,
                "context_coverage": 1.0,
                "abstention_rate": 0.0,
                "comparator_score_threshold": threshold,
            }
        )
    heldout_rows: list[YamlNode] = []
    for index, horizon in enumerate(partitions.heldout_horizons):
        stop_epoch = _comparator_stop(scores, horizon.epoch_indexes, threshold)
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
        loaded.material_digest,
        (
            method_digest,
            file_sha256(rank_path),
            file_sha256(split_path),
            file_sha256(partitions_path),
        ),
    )
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    staging = layout.roots.outputs_root / "cache" / "staging"
    evaluation_id = _evaluation_artifact_id(experiment_name, execution_role, method_name, seed)
    raw_path = (
        root
        / "evaluations"
        / "raw"
        / execution_role.value
        / _method_slug(method_name)
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
        "calibration": {"global": {"threshold": threshold}, "local": []},
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
            / _method_slug(method_name)
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
        semantic_cell_path=f"{execution_role.value}/{_method_slug(method_name)}/seed-{seed}",
        method_name=method_name,
        seed=seed,
        state=ExperimentState.COMPLETED,
        material_digest=loaded.material_digest,
        selected_client_ids=ranks.selected_client_ids,
        upstream_artifact_ids=(
            _rank_artifact_id(dataset_name, seed),
            layer_artifact_id(dataset_name, PreprocessingLayer.PARTITIONS),
            layer_artifact_id(dataset_name, PreprocessingLayer.CAMPAIGN_REGISTRY),
        ),
        dependency_fingerprint=fingerprint,
        runtime_seconds=0.0,
        peak_rss_bytes=0,
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
        / f"cell-{execution_role.value}-{_method_slug(method_name)}-seed-{seed}.json"
    )
    write_atomic_json(cell_path, cast(YamlNode, cell.model_dump(mode="json")), staging)
    return cell_path


def _execute_real_emhi_methods(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> tuple[RecordCount, tuple[MethodName, ...]]:
    contract = _experiment_contract(loaded.values, experiment_name)
    dataset_name = _experiment_dataset(loaded, experiment_name)
    supported = tuple(
        method for method in contract.methods if _emhi_method_specification(method) is not None
    )
    missing = tuple(
        method for method in contract.methods if _emhi_method_specification(method) is None
    )
    completed: RecordCount = 0
    _inventory_path, prepared_path, _split_path, _partitions_path, _campaigns_path = (
        _preprocessing_paths(loaded, repository, dataset_name)
    )
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    if not prepared.selected_client_ids:
        for role in contract.execution_roles:
            for seed in _role_seeds(loaded, role):
                for method_name in contract.methods:
                    _materialize_not_tested_real_cell(
                        loaded,
                        repository,
                        experiment_name,
                        role,
                        method_name,
                        seed,
                    )
                    completed += 1
        return completed, ()
    for role in contract.execution_roles:
        for seed in _role_seeds(loaded, role):
            score_path = _materialize_detector_scores(loaded, repository, dataset_name, seed)
            rank_path = _materialize_marginal_ranks(
                loaded,
                repository,
                dataset_name,
                seed,
                score_path,
            )
            for method_name in supported:
                fit_path = _materialize_emhi_fit(
                    loaded,
                    repository,
                    dataset_name,
                    seed,
                    method_name,
                    score_path,
                    rank_path,
                )
                _evaluate_emhi_seed_cell(
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
            for method_name in missing:
                _evaluate_comparator_seed_cell(
                    loaded,
                    repository,
                    experiment_name,
                    role,
                    method_name,
                    seed,
                    rank_path,
                )
                completed += 1
    return completed, ()


def execute_experiment(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    overwrite_policy: OverwritePolicy,
) -> ExperimentExecutionResult:
    validate_scientific_implementation_registry(loaded.values, experiment_name)
    reusable = _existing_completed_run(
        loaded,
        repository,
        experiment_name,
        overwrite_policy,
    )
    if reusable is not None:
        return reusable
    if experiment_name is ExperimentName.SYNTHETIC_MODULE_VALIDATION:
        return _execute_synthetic_module_validation(loaded, repository, overwrite_policy)
    contract = _experiment_contract(loaded.values, experiment_name)
    if not contract.uses_real_seeds:
        return _execute_synthetic_experiment(
            loaded,
            repository,
            experiment_name,
            overwrite_policy,
        )
    required = _required_preprocessing_artifacts(loaded, repository, experiment_name)
    if any(not path.is_file() for path in required):
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
    if not contract.methods:
        prepared_path = _preprocessing_paths(
            loaded, repository, _experiment_dataset(loaded, experiment_name)
        )[1]
        prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
        completed = 0
        for role in contract.execution_roles:
            for seed in _role_seeds(loaded, role):
                _materialize_not_tested_real_cell(
                    loaded,
                    repository,
                    experiment_name,
                    role,
                    None,
                    seed,
                )
                completed += 1
        detail = (
            "coordinate experiment completed as Not Tested: no eligible raw records"
            if not prepared.selected_client_ids
            else "coordinate experiment producer cells completed"
        )
        run_path = publish_experiment_run_record(
            loaded,
            repository,
            experiment_name,
            overwrite_policy,
            ExperimentState.COMPLETED,
        )
        return ExperimentExecutionResult(
            experiment_name=experiment_name,
            state=ExperimentState.COMPLETED,
            run_record_path=run_path,
            completed_cell_count=completed,
            detail=detail,
        )
    completed, _terminal_method_gaps = _execute_real_emhi_methods(
        loaded,
        repository,
        experiment_name,
    )
    _materialize_seed_statistics(loaded, repository, experiment_name)
    state = ExperimentState.COMPLETED
    run_path = publish_experiment_run_record(
        loaded,
        repository,
        experiment_name,
        overwrite_policy,
        state,
    )
    detail = "all configured real-data method cells completed"
    return ExperimentExecutionResult(
        experiment_name=experiment_name,
        state=state,
        run_record_path=run_path,
        completed_cell_count=completed,
        detail=detail,
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
