import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from time import perf_counter
from typing import cast

from fedcampaign_emhi.analysis.multiplicity import holm_adjusted_p_values
from fedcampaign_emhi.analysis.statistics import (
    exact_sign_flip_means,
    mean_bca_one_sided_lower_bound,
    one_sided_synthetic_sign_flip_p_value,
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
    EstimatorFeasibilityAggregationRecord,
    ExperimentRunRecord,
    FiniteHorizonAggregationRecord,
    MarginalRankArtifactRecord,
    PlanArtifactRecord,
    PlannedExperimentRecord,
    PreparedDatasetRecord,
    ScientificCellRecord,
    SeedSummaryRecord,
    StatisticalRecord,
    StrongComparatorCompositionRecord,
)
from fedcampaign_emhi.artifacts.storage import file_sha256, payload_digest, write_atomic_json
from fedcampaign_emhi.comparators.contracts import (
    ComparatorMethodContract,
    comparator_method_contracts,
    native_target_order,
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
    PrimaryHolmHypothesis,
    SupportState,
)
from fedcampaign_emhi.domain.types import (
    ArtifactIdentity,
    Boolean,
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
from fedcampaign_emhi.emhi.evidence import (
    operational_evidence_factor,
    operational_norm_reference_quantile,
)
from fedcampaign_emhi.emhi.innovation_calibration import build_emhi_fit_artifact
from fedcampaign_emhi.emhi.ranks import build_marginal_rank_artifact
from fedcampaign_emhi.emhi.sequential import next_global_state
from fedcampaign_emhi.emhi.thresholds import (
    clopper_pearson_one_sided_upper_bound,
    select_calibrated_threshold,
)
from fedcampaign_emhi.evaluation.benign_horizons import (
    TrajectoryCache,
    calibrate_client_local_operating_point,
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
from fedcampaign_emhi.evaluation.smoke_validation import run_synthetic_module_validation
from fedcampaign_emhi.execution.finite_horizon import (
    FiniteHorizonSeedMetrics,
    evaluate_finite_horizon_common_mode_seed,
)
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE, plan_experiments
from fedcampaign_emhi.execution.preprocess import dataset_directory_stem, layer_artifact_id
from fedcampaign_emhi.execution.pure_order import (
    emhi_method_settings,
    evaluate_comparator_pure_order_cell,
    evaluate_fitted_pure_order_cell,
)
from fedcampaign_emhi.experiments.definitions import ExperimentContract, experiment_registry
from fedcampaign_emhi.experiments.producers import (
    EstimatorFeasibilitySeedMetrics,
    PureOrderSeedMetrics,
    SelfExplanationSeedMetrics,
    SyntheticCellOutcome,
    run_synthetic_cell,
    synthetic_role_seeds,
)
from fedcampaign_emhi.experiments.validation import assert_known_experiment
from fedcampaign_emhi.synthetic.pure_order import enumerate_pure_order_grid
from fedcampaign_emhi.synthetic.sequential import SignedTheoremSeedMetrics
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
    purification_enabled: Boolean


@dataclass(frozen=True)
class SelfExplanationObservation:
    execution_role: ExecutionRole
    seed: SeedValue
    metric: SelfExplanationSeedMetrics
    diagnostic_path: Path


@dataclass(frozen=True)
class PureOrderObservation:
    execution_role: ExecutionRole
    seed: SeedValue
    metric: PureOrderSeedMetrics
    diagnostic_path: Path


@dataclass(frozen=True)
class SignedTheoremObservation:
    execution_role: ExecutionRole
    seed: SeedValue
    metric: SignedTheoremSeedMetrics
    diagnostic_path: Path


@dataclass(frozen=True)
class FiniteHorizonObservation:
    execution_role: ExecutionRole
    seed: SeedValue
    metric: FiniteHorizonSeedMetrics
    diagnostic_path: Path


@dataclass(frozen=True)
class EstimatorFeasibilityObservation:
    execution_role: ExecutionRole
    seed: SeedValue
    metric: EstimatorFeasibilitySeedMetrics
    diagnostic_path: Path


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
) -> Boolean:
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
    invariant_criterion = run_synthetic_module_validation(loaded)
    generator_criterion = validate_synthetic_generators(loaded)
    state = (
        ExperimentState.COMPLETED
        if invariant_criterion.passed and generator_criterion.state is ExperimentState.COMPLETED
        else ExperimentState.INVALID
    )
    diagnostic_path = root / "diagnostics" / "scientific" / "synthetic-validation.json"
    diagnostic_payload: YamlNode = {
        "state": state.value,
        "invariant_failures": [failure.label for failure in invariant_criterion.failures],
        "generator_failures": list(generator_criterion.failed_checks),
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
    completed = 0
    invalid = 0
    self_explanation_observations: list[SelfExplanationObservation] = []
    pure_order_observations: list[PureOrderObservation] = []
    signed_theorem_observations: list[SignedTheoremObservation] = []
    finite_horizon_observations: list[FiniteHorizonObservation] = []
    estimator_feasibility_observations: list[EstimatorFeasibilityObservation] = []
    for role in contract.execution_roles:
        methods: tuple[MethodName | None, ...] = contract.methods or (None,)
        for seed in synthetic_role_seeds(loaded, role):
            for method_name in methods:
                started = perf_counter()
                finite_horizon_metrics: FiniteHorizonSeedMetrics | None = None
                try:
                    outcome = run_synthetic_cell(loaded, experiment_name, seed, method_name, role)
                    if (
                        experiment_name is ExperimentName.PURE_ORDER_SEPARATION_VALIDATION
                        and method_name is not None
                        and emhi_method_settings(method_name) is not None
                    ):
                        primary = loaded.values.experiments.pure_order_separation_validation.primary_condition
                        fitted_grid = tuple(
                            (cell, evaluate_fitted_pure_order_cell(loaded.values, cell, seed))
                            for cell in enumerate_pure_order_grid(loaded.values)
                            if cell.method is method_name
                        )
                        primary_fitted = (
                            next(
                                (
                                    fitted
                                    for cell, fitted in fitted_grid
                                    if cell.generator is primary.generator
                                    and cell.target_order == CoalitionOrder(primary.coalition_order)
                                    and cell.effect
                                    == loaded.values.generators.pure_polynomial.primary_reference_theta
                                ),
                                None,
                            )
                            if method_name is primary.method
                            else None
                        )
                        grid_complete = all(
                            fitted is not None and fitted.artifact_path_complete
                            for _cell, fitted in fitted_grid
                        )
                        if grid_complete:
                            evidence = dict(cast(Mapping[str, YamlNode], outcome.evidence))
                            evidence["exact_exclusion_artifact_grid_complete"] = grid_complete
                            evidence["implementation_state"] = "fitted_emhi_artifact_grid"
                            evidence["fitted_emhi_scores"] = [
                                {
                                    "generator": cell.generator.value,
                                    "effect": cell.effect,
                                    "target_order": int(cell.target_order),
                                    "maximum_proper_subset_standardized_drift": fitted.metrics.maximum_proper_subset_standardized_drift,
                                    "target_order_standardized_drift": fitted.metrics.target_order_standardized_drift,
                                }
                                for cell, fitted in fitted_grid
                                if fitted is not None
                            ]
                            if primary_fitted is not None and primary_fitted.artifact_path_complete:
                                evidence["primary_exact_exclusion_artifact_score"] = {
                                    "maximum_proper_subset_standardized_drift": primary_fitted.metrics.maximum_proper_subset_standardized_drift,
                                    "target_order_standardized_drift": primary_fitted.metrics.target_order_standardized_drift,
                                }
                            outcome = replace(
                                outcome,
                                evidence=evidence,
                                pure_order_metrics=(
                                    PureOrderSeedMetrics(
                                        primary_fitted.metrics.maximum_proper_subset_standardized_drift,
                                        primary_fitted.metrics.target_order_standardized_drift,
                                    )
                                    if primary_fitted is not None
                                    and primary_fitted.artifact_path_complete
                                    else outcome.pure_order_metrics
                                ),
                                failed_checks=outcome.failed_checks,
                            )
                        else:
                            outcome = replace(
                                outcome,
                                failed_checks=(
                                    *outcome.failed_checks,
                                    "incomplete fitted EMHI pure-order grid",
                                ),
                            )
                    if (
                        experiment_name is ExperimentName.PURE_ORDER_SEPARATION_VALIDATION
                        and method_name is not None
                        and emhi_method_settings(method_name) is None
                        and method_name
                        is not loaded.values.experiments.pure_order_separation_validation.primary_condition.method
                    ):
                        comparator_grid = tuple(
                            (cell, evaluate_comparator_pure_order_cell(loaded.values, cell, seed))
                            for cell in enumerate_pure_order_grid(loaded.values)
                            if cell.method is method_name
                        )
                        native_order = native_target_order(method_name)
                        expected_comparator_cells = tuple(
                            cell
                            for cell, _metrics in comparator_grid
                            if native_order is not None and cell.target_order is native_order
                        )
                        comparator_completed = tuple(
                            (cell, metrics)
                            for cell, metrics in comparator_grid
                            if metrics is not None
                        )
                        comparator_grid_complete = bool(expected_comparator_cells) and all(
                            metrics is not None
                            for cell, metrics in comparator_grid
                            if cell in expected_comparator_cells
                        )
                        if comparator_completed:
                            evidence = dict(cast(Mapping[str, YamlNode], outcome.evidence))
                            evidence["native_comparator_scores"] = [
                                {
                                    "generator": cell.generator.value,
                                    "effect": cell.effect,
                                    "target_order": int(cell.target_order),
                                    "target_order_standardized_drift": metrics.target_order_standardized_drift,
                                }
                                for cell, metrics in comparator_completed
                            ]
                            evidence["native_comparator_grid"] = {
                                "native_target_order": int(native_order)
                                if native_order is not None
                                else None,
                                "expected_cell_count": len(expected_comparator_cells),
                                "completed_cell_count": len(comparator_completed),
                                "complete": comparator_grid_complete,
                            }
                            if comparator_grid_complete:
                                evidence["implementation_state"] = "native_comparator_grid"
                            outcome = replace(
                                outcome,
                                evidence=evidence,
                                failed_checks=(
                                    outcome.failed_checks
                                    if comparator_grid_complete
                                    else (
                                        *outcome.failed_checks,
                                        "incomplete native comparator pure-order grid",
                                    )
                                ),
                            )
                    if experiment_name is ExperimentName.SEQUENTIAL_EVIDENCE_VALIDATION:
                        finite_horizon = evaluate_finite_horizon_common_mode_seed(
                            loaded.values, seed
                        )
                        finite_horizon_metrics = finite_horizon.metrics
                        evidence = dict(cast(Mapping[str, YamlNode], outcome.evidence))
                        evidence["calibrated_finite_horizon"] = {
                            "calibrated_threshold": finite_horizon.metrics.calibrated_threshold,
                            "calibration_horizon_count": finite_horizon.metrics.calibration_horizon_count,
                            "heldout_horizon_count": finite_horizon.metrics.heldout_horizon_count,
                            "heldout_false_stop_count": finite_horizon.metrics.heldout_false_stop_count,
                            "heldout_upper_pfa": finite_horizon.metrics.heldout_upper_pfa,
                            "operating_point_available": finite_horizon.metrics.calibrated_threshold
                            is not None,
                        }
                        outcome = replace(
                            outcome,
                            evidence=evidence,
                            failed_checks=(
                                outcome.failed_checks
                                if finite_horizon.assumptions_hold
                                else (
                                    *outcome.failed_checks,
                                    "finite-horizon operational-route assumptions",
                                )
                            ),
                        )
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
                if (
                    state is ExperimentState.COMPLETED
                    and outcome.self_explanation_metrics is not None
                ):
                    self_explanation_observations.append(
                        SelfExplanationObservation(
                            execution_role=role,
                            seed=seed,
                            metric=outcome.self_explanation_metrics,
                            diagnostic_path=diagnostic_path,
                        )
                    )
                if state is ExperimentState.COMPLETED and outcome.pure_order_metrics is not None:
                    pure_order_observations.append(
                        PureOrderObservation(
                            execution_role=role,
                            seed=seed,
                            metric=outcome.pure_order_metrics,
                            diagnostic_path=diagnostic_path,
                        )
                    )
                if (
                    state is ExperimentState.COMPLETED
                    and outcome.signed_theorem_metrics is not None
                ):
                    signed_theorem_observations.append(
                        SignedTheoremObservation(
                            execution_role=role,
                            seed=seed,
                            metric=outcome.signed_theorem_metrics,
                            diagnostic_path=diagnostic_path,
                        )
                    )
                if state is ExperimentState.COMPLETED and finite_horizon_metrics is not None:
                    finite_horizon_observations.append(
                        FiniteHorizonObservation(
                            execution_role=role,
                            seed=seed,
                            metric=finite_horizon_metrics,
                            diagnostic_path=diagnostic_path,
                        )
                    )
                if (
                    state is ExperimentState.COMPLETED
                    and outcome.estimator_feasibility_metrics is not None
                ):
                    estimator_feasibility_observations.append(
                        EstimatorFeasibilityObservation(
                            execution_role=role,
                            seed=seed,
                            metric=outcome.estimator_feasibility_metrics,
                            diagnostic_path=diagnostic_path,
                        )
                    )
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
    if experiment_name is ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION:
        materialize_self_explanation_statistics(
            loaded,
            repository,
            tuple(self_explanation_observations),
        )
    if experiment_name is ExperimentName.PURE_ORDER_SEPARATION_VALIDATION:
        materialize_pure_order_statistics(loaded, repository, tuple(pure_order_observations))
    if experiment_name is ExperimentName.SEQUENTIAL_EVIDENCE_VALIDATION:
        materialize_signed_theorem_statistics(
            loaded,
            repository,
            tuple(signed_theorem_observations),
        )
        materialize_finite_horizon_statistics(
            loaded,
            repository,
            tuple(finite_horizon_observations),
        )
    if experiment_name is ExperimentName.ESTIMATOR_SUPPORT_AND_CONTEXT_FEASIBILITY:
        materialize_estimator_feasibility_statistics(
            loaded,
            repository,
            tuple(estimator_feasibility_observations),
        )
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


def materialize_self_explanation_statistics(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    observations: tuple[SelfExplanationObservation, ...],
) -> Path | None:
    confirmatory = tuple(
        observation
        for observation in observations
        if observation.execution_role is ExecutionRole.CONFIRMATORY
    )
    expected = loaded.values.randomness.synthetic_confirmatory_roots
    if tuple(observation.seed for observation in confirmatory) != expected:
        return None
    values = tuple(observation.metric.primary_attenuation_contrast for observation in confirmatory)
    raw_p_value = one_sided_synthetic_sign_flip_p_value(
        values,
        loaded.values.statistics.synthetic_sign_flip_replicates_when_not_exact,
        loaded.values.statistics.synthetic_sign_flip_replicates_when_not_exact,
        loaded.values.randomness.statistical_analysis_base_seed,
    )
    interval = paired_mean_bca_interval(
        values,
        loaded.values.statistics.confidence_level,
        loaded.values.statistics.bootstrap_replicates,
        loaded.values.randomness.statistical_analysis_base_seed,
    )
    layout = build_artifact_layout(loaded, repository)
    source_paths = tuple(observation.diagnostic_path for observation in confirmatory)
    source_digests = tuple(file_sha256(path) for path in source_paths)
    source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
    payload: YamlNode = {
        "experiment_name": ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION.value,
        "hypothesis_identifier": "Self-Explanation Material Attenuation",
        "metric_name": "primary_attenuation_contrast",
        "method_name": "Exact Complement Exclusion",
        "independent_unit_count": len(values),
        "estimate": sum(values) / len(values),
        "raw_p_value": raw_p_value,
        "confidence_level": loaded.values.statistics.confidence_level,
        "confidence_lower": interval[0],
        "confidence_upper": interval[1],
        "source_result_ids": list(source_ids),
    }
    record = StatisticalRecord(
        hypothesis_identifier="Self-Explanation Material Attenuation",
        metric_name="primary_attenuation_contrast",
        method_name="Exact Complement Exclusion",
        independent_unit_count=len(values),
        estimate=sum(values) / len(values),
        raw_p_value=raw_p_value,
        adjusted_p_value=None,
        confidence_level=loaded.values.statistics.confidence_level,
        confidence_lower=interval[0],
        confidence_upper=interval[1],
        decision=(
            SupportState.SUPPORTED
            if raw_p_value < loaded.values.statistics.nominal_significance_alpha
            else SupportState.NULL_RESULT
        ),
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(loaded.material_digest, source_digests),
        content_digest=payload_digest(payload),
    )
    path = (
        layout.experiment_outputs_root(ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION)
        / "statistics"
        / "tests"
        / "self-explanation-material-attenuation.json"
    )
    staging = layout.roots.outputs_root / "cache" / "staging"
    write_atomic_json(path, cast(YamlNode, record.model_dump(mode="json")), staging)
    return path


def materialize_pure_order_statistics(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    observations: tuple[PureOrderObservation, ...],
) -> Path | None:
    confirmatory = tuple(
        observation
        for observation in observations
        if observation.execution_role is ExecutionRole.CONFIRMATORY
    )
    expected = loaded.values.randomness.synthetic_confirmatory_roots
    if tuple(observation.seed for observation in confirmatory) != expected:
        return None
    values = tuple(
        observation.metric.target_order_standardized_drift for observation in confirmatory
    )
    raw_p_value = one_sided_synthetic_sign_flip_p_value(
        values,
        loaded.values.statistics.synthetic_sign_flip_replicates_when_not_exact,
        loaded.values.statistics.synthetic_sign_flip_replicates_when_not_exact,
        loaded.values.randomness.statistical_analysis_base_seed,
    )
    interval = paired_mean_bca_interval(
        values,
        loaded.values.statistics.confidence_level,
        loaded.values.statistics.bootstrap_replicates,
        loaded.values.randomness.statistical_analysis_base_seed,
    )
    layout = build_artifact_layout(loaded, repository)
    source_paths = tuple(observation.diagnostic_path for observation in confirmatory)
    source_digests = tuple(file_sha256(path) for path in source_paths)
    source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
    payload: YamlNode = {
        "experiment_name": ExperimentName.PURE_ORDER_SEPARATION_VALIDATION.value,
        "hypothesis_identifier": "Pure-Order Target Drift",
        "metric_name": "target_order_standardized_drift",
        "method_name": MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        "independent_unit_count": len(values),
        "estimate": sum(values) / len(values),
        "raw_p_value": raw_p_value,
        "confidence_level": loaded.values.statistics.confidence_level,
        "confidence_lower": interval[0],
        "confidence_upper": interval[1],
        "source_result_ids": list(source_ids),
    }
    record = StatisticalRecord(
        hypothesis_identifier="Pure-Order Target Drift",
        metric_name="target_order_standardized_drift",
        method_name=MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        independent_unit_count=len(values),
        estimate=sum(values) / len(values),
        raw_p_value=raw_p_value,
        adjusted_p_value=None,
        confidence_level=loaded.values.statistics.confidence_level,
        confidence_lower=interval[0],
        confidence_upper=interval[1],
        decision=(
            SupportState.SUPPORTED
            if raw_p_value < loaded.values.statistics.nominal_significance_alpha
            else SupportState.NULL_RESULT
        ),
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(loaded.material_digest, source_digests),
        content_digest=payload_digest(payload),
    )
    path = (
        layout.experiment_outputs_root(ExperimentName.PURE_ORDER_SEPARATION_VALIDATION)
        / "statistics"
        / "tests"
        / "pure-order-target-drift.json"
    )
    staging = layout.roots.outputs_root / "cache" / "staging"
    write_atomic_json(path, cast(YamlNode, record.model_dump(mode="json")), staging)
    return path


def materialize_estimator_feasibility_statistics(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    observations: tuple[EstimatorFeasibilityObservation, ...],
) -> Path | None:
    confirmatory = tuple(
        observation
        for observation in observations
        if observation.execution_role is ExecutionRole.CONFIRMATORY
    )
    expected = loaded.values.randomness.synthetic_confirmatory_roots
    if tuple(observation.seed for observation in confirmatory) != expected:
        return None
    metrics = tuple(observation.metric.primary for observation in confirmatory)
    failure_count = sum(metric.numerical_failure for metric in metrics)
    failure_rate = failure_count / len(metrics)
    materiality = loaded.values.materiality
    decision = (
        SupportState.SUPPORTED
        if (
            sum(metric.context_coverage for metric in metrics) / len(metrics)
            >= materiality.order_three_estimator.minimum_mean_context_coverage
            and sum(metric.projection_nrmse for metric in metrics) / len(metrics)
            <= materiality.order_three_estimator.maximum_mean_projection_nrmse
            and sum(metric.standardized_null_bias for metric in metrics) / len(metrics)
            <= materiality.order_three_estimator.maximum_mean_standardized_null_bias
            and failure_rate <= materiality.maximum_pooled_numerical_failure_rate
        )
        else SupportState.NULL_RESULT
    )
    layout = build_artifact_layout(loaded, repository)
    source_paths = tuple(observation.diagnostic_path for observation in confirmatory)
    source_digests = tuple(file_sha256(path) for path in source_paths)
    source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
    payload: YamlNode = {
        "experiment_name": ExperimentName.ESTIMATOR_SUPPORT_AND_CONTEXT_FEASIBILITY.value,
        "independent_unit_count": len(metrics),
        "mean_context_coverage": sum(metric.context_coverage for metric in metrics) / len(metrics),
        "mean_projection_nrmse": sum(metric.projection_nrmse for metric in metrics) / len(metrics),
        "mean_standardized_null_bias": sum(metric.standardized_null_bias for metric in metrics)
        / len(metrics),
        "numerical_failure_count": failure_count,
        "attempted_condition_count": len(metrics),
        "pooled_numerical_failure_rate": failure_rate,
        "decision": decision.value,
        "source_result_ids": list(source_ids),
    }
    record = EstimatorFeasibilityAggregationRecord(
        experiment_name=ExperimentName.ESTIMATOR_SUPPORT_AND_CONTEXT_FEASIBILITY,
        independent_unit_count=len(metrics),
        mean_context_coverage=sum(metric.context_coverage for metric in metrics) / len(metrics),
        mean_projection_nrmse=sum(metric.projection_nrmse for metric in metrics) / len(metrics),
        mean_standardized_null_bias=sum(metric.standardized_null_bias for metric in metrics)
        / len(metrics),
        numerical_failure_count=failure_count,
        attempted_condition_count=len(metrics),
        pooled_numerical_failure_rate=failure_rate,
        decision=decision,
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(loaded.material_digest, source_digests),
        content_digest=payload_digest(payload),
    )
    path = (
        layout.experiment_outputs_root(ExperimentName.ESTIMATOR_SUPPORT_AND_CONTEXT_FEASIBILITY)
        / "statistics"
        / "tests"
        / "estimator-order-three-feasibility.json"
    )
    staging = layout.roots.outputs_root / "cache" / "staging"
    write_atomic_json(path, cast(YamlNode, record.model_dump(mode="json")), staging)
    return path


def materialize_signed_theorem_statistics(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    observations: tuple[SignedTheoremObservation, ...],
) -> Path | None:
    confirmatory = tuple(
        observation
        for observation in observations
        if observation.execution_role is ExecutionRole.CONFIRMATORY
    )
    expected = loaded.values.randomness.synthetic_confirmatory_roots
    if tuple(observation.seed for observation in confirmatory) != expected:
        return None
    values = tuple(observation.metric.restricted_arl for observation in confirmatory)
    confidence_level = loaded.values.statistics.confidence_level
    lower = mean_bca_one_sided_lower_bound(
        values,
        confidence_level,
        loaded.values.statistics.bootstrap_replicates,
        loaded.values.randomness.statistical_analysis_base_seed,
    )
    layout = build_artifact_layout(loaded, repository)
    source_paths = tuple(observation.diagnostic_path for observation in confirmatory)
    source_digests = tuple(file_sha256(path) for path in source_paths)
    source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
    threshold = loaded.values.experiments.sequential_evidence_validation.signed_theorem.restricted_arl_bootstrap_lower_bound_minimum_epochs
    payload: YamlNode = {
        "experiment_name": ExperimentName.SEQUENTIAL_EVIDENCE_VALIDATION.value,
        "hypothesis_identifier": "Signed-Theorem Restricted ARL",
        "metric_name": "restricted_arl",
        "method_name": "Signed-Theorem Sequential Route",
        "independent_unit_count": len(values),
        "estimate": sum(values) / len(values),
        "raw_p_value": None,
        "confidence_level": confidence_level,
        "confidence_lower": lower,
        "confidence_upper": None,
        "source_result_ids": list(source_ids),
    }
    record = StatisticalRecord(
        hypothesis_identifier="Signed-Theorem Restricted ARL",
        metric_name="restricted_arl",
        method_name="Signed-Theorem Sequential Route",
        independent_unit_count=len(values),
        estimate=sum(values) / len(values),
        raw_p_value=None,
        adjusted_p_value=None,
        confidence_level=confidence_level,
        confidence_lower=lower,
        confidence_upper=None,
        decision=(SupportState.SUPPORTED if lower >= threshold else SupportState.NULL_RESULT),
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(loaded.material_digest, source_digests),
        content_digest=payload_digest(payload),
    )
    path = (
        layout.experiment_outputs_root(ExperimentName.SEQUENTIAL_EVIDENCE_VALIDATION)
        / "statistics"
        / "tests"
        / "signed-theorem-restricted-arl.json"
    )
    staging = layout.roots.outputs_root / "cache" / "staging"
    write_atomic_json(path, cast(YamlNode, record.model_dump(mode="json")), staging)
    return path


def materialize_finite_horizon_statistics(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    observations: tuple[FiniteHorizonObservation, ...],
) -> Path | None:
    confirmatory = tuple(
        observation
        for observation in observations
        if observation.execution_role is ExecutionRole.CONFIRMATORY
    )
    expected = loaded.values.randomness.synthetic_confirmatory_roots
    if tuple(observation.seed for observation in confirmatory) != expected:
        return None
    unavailable_count = sum(
        observation.metric.calibrated_threshold is None for observation in confirmatory
    )
    upper_bounds = tuple(
        observation.metric.heldout_upper_pfa
        for observation in confirmatory
        if observation.metric.heldout_upper_pfa is not None
    )
    maximum_upper = max(upper_bounds, default=None)
    target = loaded.values.evidence.calibrated_finite_horizon.target_pfa
    decision = (
        SupportState.NOT_SUPPORTED
        if unavailable_count > 0
        else (
            SupportState.SUPPORTED
            if maximum_upper is not None and maximum_upper <= target
            else SupportState.NULL_RESULT
        )
    )
    layout = build_artifact_layout(loaded, repository)
    source_paths = tuple(observation.diagnostic_path for observation in confirmatory)
    source_digests = tuple(file_sha256(path) for path in source_paths)
    source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
    payload: YamlNode = {
        "experiment_name": ExperimentName.SEQUENTIAL_EVIDENCE_VALIDATION.value,
        "independent_unit_count": len(confirmatory),
        "operating_point_unavailable_count": unavailable_count,
        "target_pfa": target,
        "maximum_heldout_upper_pfa": maximum_upper,
        "decision": decision.value,
        "source_result_ids": list(source_ids),
    }
    record = FiniteHorizonAggregationRecord(
        experiment_name=ExperimentName.SEQUENTIAL_EVIDENCE_VALIDATION,
        independent_unit_count=len(confirmatory),
        operating_point_unavailable_count=unavailable_count,
        target_pfa=target,
        maximum_heldout_upper_pfa=maximum_upper,
        decision=decision,
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(loaded.material_digest, source_digests),
        content_digest=payload_digest(payload),
    )
    path = (
        layout.experiment_outputs_root(ExperimentName.SEQUENTIAL_EVIDENCE_VALIDATION)
        / "statistics"
        / "tests"
        / "calibrated-finite-horizon-pfa.json"
    )
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    return path


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
    campaign_rows, odi_values = _campaign_rows(
        loaded,
        scores,
        ranks,
        fit,
        campaigns,
        calibration,
    )
    heldout_rows = _heldout_rows(loaded, ranks, fit, partitions, calibration, trajectory_cache)
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
        "support_state": "NOT_TESTED",
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


def resolve_comparator_scoring_method(
    loaded: LoadedScientificConfiguration, repository: Path, method_name: MethodName
) -> MethodName:
    if method_name is not MethodName.SELECTED_STRONG_COMPARATOR_COMPOSITION:
        return method_name
    layout = build_artifact_layout(loaded, repository)
    filename = loaded.values.experiments.strong_comparator_composition_challenge.artifact_filename
    path = (
        layout.experiment_outputs_root(ExperimentName.STRONG_COMPARATOR_COMPOSITION_CHALLENGE)
        / "artifacts"
        / "derived"
        / filename
    )
    if not path.is_file():
        raise ValueError("selected strong comparator requires a validated composition artifact")
    record = StrongComparatorCompositionRecord.model_validate_json(path.read_bytes())
    payload = record.model_dump(mode="json", exclude={"dependency_fingerprint", "content_digest"})
    if payload_digest(cast(YamlNode, payload)) != record.content_digest:
        raise ValueError("selected strong comparator artifact content digest is invalid")
    if record.dependency_fingerprint != material_fingerprint(
        loaded.material_digest, record.source_artifact_hashes
    ):
        raise ValueError("selected strong comparator artifact dependency fingerprint is stale")
    if record.selected_method not in record.eligible_candidates:
        raise ValueError("selected strong comparator artifact selected an ineligible candidate")
    if native_target_order(record.selected_method) is not record.selected_native_order:
        raise ValueError("selected strong comparator artifact native-order mapping is invalid")
    return record.selected_method


def _comparator_epoch_scores(
    loaded: LoadedScientificConfiguration,
    repository: Path,
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
    scoring_method = resolve_comparator_scoring_method(loaded, repository, method_name)
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


def _comparator_evidence_scores(
    loaded: LoadedScientificConfiguration,
    raw_scores: tuple[tuple[EpochIndexValue, FiniteFloat], ...],
    nuisance_epochs: tuple[EpochIndexValue, ...],
) -> tuple[tuple[EpochIndexValue, FiniteFloat], ...]:
    nuisance_scores = tuple(score for epoch, score in raw_scores if epoch in nuisance_epochs)
    if not nuisance_scores:
        raise ValueError("comparator evidence requires nuisance-fit scores")
    nuisance_mean = sum(nuisance_scores) / len(nuisance_scores)
    nuisance_deviation = (
        sum((score - nuisance_mean) ** 2 for score in nuisance_scores) / len(nuisance_scores)
    ) ** 0.5
    floor = loaded.values.numerics.metric_denominator_floor
    if nuisance_deviation <= floor:
        raise ValueError("comparator nuisance-fit score deviation is not usable")
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


def _comparator_stop(
    evidence_scores: tuple[tuple[EpochIndexValue, FiniteFloat], ...],
    epochs: tuple[EpochIndexValue, ...],
    threshold: FiniteFloat | None,
) -> EpochIndexValue | None:
    if threshold is None:
        return None
    state = 0.0
    for epoch in epochs:
        factor = next(
            (score for score_epoch, score in evidence_scores if score_epoch == epoch),
            None,
        )
        if factor is None:
            continue
        state = next_global_state(state, factor)
        if state >= threshold:
            return epoch
    return None


def _calibrate_comparator_operating_point(
    loaded: LoadedScientificConfiguration,
    evidence_scores: tuple[tuple[EpochIndexValue, FiniteFloat], ...],
    partitions: BenignPartitionRecord,
) -> tuple[
    FiniteFloat | None, tuple[RecordCount, ...], RecordCount, RecordCount, FiniteFloat | None
]:
    calibration_horizons = partitions.calibration_horizons
    heldout_horizons = partitions.heldout_horizons
    candidates = loaded.values.evidence.calibrated_finite_horizon.threshold_candidates
    calibration_counts = tuple(
        sum(
            _comparator_stop(evidence_scores, horizon.epoch_indexes, threshold) is not None
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
        _comparator_stop(evidence_scores, horizon.epoch_indexes, selected) is not None
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
            SupportState.SUPPORTED
            if adjusted[index] < loaded.values.statistics.nominal_significance_alpha
            else SupportState.NULL_RESULT
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


def _materialize_not_tested_primary_holm_statistic(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> Path | None:
    hypotheses = {
        ExperimentName.PRIMARY_STRICT_ODI_EVALUATION: (
            PrimaryHolmHypothesis.PRIMARY_ODI_ADVANTAGE_OVER_ORDER_AT_MOST_TWO_EMHI,
            "paired_strict_odi_rate_advantage",
        ),
        ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS: (
            PrimaryHolmHypothesis.COMMON_MODE_FALSE_CAMPAIGN_REDUCTION,
            "false_campaign_reduction",
        ),
        ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE: (
            PrimaryHolmHypothesis.STRONG_LOCAL_ODI_ABOVE_MINIMUM,
            "strong_local_strict_odi_rate",
        ),
    }
    specification = hypotheses.get(experiment_name)
    if specification is None:
        return None
    dataset_name = _experiment_dataset(loaded, experiment_name)
    prepared_path = _preprocessing_paths(loaded, repository, dataset_name)[1]
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    if (
        prepared.selection_support_state is not SupportState.NOT_TESTED
        or prepared.selected_client_ids
    ):
        return None
    hypothesis, metric_name = specification
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    source_paths = tuple(
        sorted(
            (
                root
                / "evaluations"
                / "raw"
                / ExecutionRole.CONFIRMATORY.value
                / _method_slug(MethodName.FULL_FEDCAMPAIGN_EMHI)
            ).glob("*.json")
        )
    )
    expected_seeds = loaded.values.randomness.real_confirmatory_roots
    if len(source_paths) != len(expected_seeds):
        raise FileNotFoundError(
            f"missing confirmatory Not Tested sources for {experiment_name.value}"
        )
    source_digests = tuple(file_sha256(path) for path in source_paths)
    source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
    payload: YamlNode = {
        "experiment_name": experiment_name.value,
        "hypothesis_identifier": hypothesis.value,
        "metric_name": metric_name,
        "method_name": MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        "independent_unit_count": len(source_paths),
        "estimate": 0.0,
        "raw_p_value": None,
        "confidence_level": None,
        "confidence_lower": None,
        "confidence_upper": None,
        "source_result_ids": list(source_ids),
    }
    record = StatisticalRecord(
        hypothesis_identifier=hypothesis.value,
        metric_name=metric_name,
        method_name=MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        independent_unit_count=len(source_paths),
        estimate=0.0,
        raw_p_value=None,
        adjusted_p_value=None,
        confidence_level=None,
        confidence_lower=None,
        confidence_upper=None,
        decision=SupportState.NOT_TESTED,
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(loaded.material_digest, source_digests),
        content_digest=payload_digest(payload),
    )
    path = root / "statistics" / "tests" / "primary-holm-not-tested.json"
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    return path


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
    dataset_name = _experiment_dataset(loaded, experiment_name)
    _inventory_path, _prepared_path, split_path, partitions_path, campaigns_path = (
        _preprocessing_paths(loaded, repository, dataset_name)
    )
    ranks = MarginalRankArtifactRecord.model_validate_json(rank_path.read_bytes())
    detector_scores = DetectorScoreArtifactRecord.model_validate_json(score_path.read_bytes())
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    partitions = BenignPartitionRecord.model_validate_json(partitions_path.read_bytes())
    campaigns = CampaignRegistryRecord.model_validate_json(campaigns_path.read_bytes())
    raw_scores = _comparator_epoch_scores(loaded, repository, ranks, method_name)
    scores = _comparator_evidence_scores(loaded, raw_scores, split.nuisance_fit_epochs)
    (
        threshold,
        calibration_false_stop_counts,
        calibration_horizon_count,
        heldout_false_stop_count,
        heldout_upper_pfa,
    ) = _calibrate_comparator_operating_point(loaded, scores, partitions)
    local_operating_points = tuple(
        calibrate_client_local_operating_point(
            loaded.values,
            detector_scores,
            client_id,
            split.nuisance_fit_epochs,
            partitions,
            _local_pfa_target(loaded, experiment_name),
        )
        for client_id in detector_scores.selected_client_ids
    )
    campaign_rows: list[YamlNode] = []
    odi_values: list[FiniteFloat] = []
    for campaign in campaigns.campaigns:
        started = perf_counter()
        epochs = tuple(range(campaign.start_epoch, campaign.end_epoch + 1))
        stop_epoch = _comparator_stop(scores, epochs, threshold)
        elapsed: RuntimeSeconds = perf_counter() - started
        local_stops = local_stop_epochs(detector_scores, local_operating_points, epochs)
        odi = odi_evaluation_record(stop_epoch, local_stops)
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
        odi_values.append(float(indicator))
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
            file_sha256(score_path),
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
                    score_path,
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
            detail="required deterministic preprocessing artifacts are missing",
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
    _materialize_not_tested_primary_holm_statistic(loaded, repository, experiment_name)
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
