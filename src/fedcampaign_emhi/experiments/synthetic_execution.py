import os
from collections import UserDict
from collections.abc import Iterator, Mapping, MutableMapping
from concurrent.futures import FIRST_COMPLETED, Future, ProcessPoolExecutor, wait
from dataclasses import dataclass, replace
from json import loads
from pathlib import Path
from time import perf_counter
from typing import cast

from pydantic import TypeAdapter

from fedcampaign_emhi.analysis.statistics import (
    hodges_lehmann_shift,
    interval_establishes_equivalence,
    mean_bca_one_sided_lower_bound,
    one_sided_synthetic_sign_flip_p_value,
    paired_mean_bca_interval,
)
from fedcampaign_emhi.artifacts.provenance import (
    evidence_export_boundary_digest,
    material_fingerprint,
    statistical_analysis_boundary_digest,
    synthetic_cell_boundary_digest,
    synthetic_invariant_boundary_digest,
)
from fedcampaign_emhi.artifacts.records import (
    CompletionRecord,
    EstimatorFeasibilityAggregationRecord,
    FiniteHorizonAggregationRecord,
    ScientificCellRecord,
    StatisticalRecord,
)
from fedcampaign_emhi.artifacts.storage import (
    build_artifact_layout,
    file_sha256,
    method_artifact_stem,
    payload_digest,
    write_atomic_json,
)
from fedcampaign_emhi.comparators.contracts import (
    native_target_order,
)
from fedcampaign_emhi.comparators.dependence import (
    cosine_equivalence_criterion,
    nrmse_equivalence_criterion,
    stopping_time_equivalence_criterion,
)
from fedcampaign_emhi.comparators.fusion import (
    CompositionCandidateResult,
    CompositionSelectionInputs,
    build_composition_selection_record,
    mean_standardized_error,
    median_runtime_seconds,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    CoalitionOrder,
    ExecutionRole,
    ExperimentName,
    ExperimentState,
    MethodName,
    OverwritePolicy,
    PrimaryHolmHypothesis,
)
from fedcampaign_emhi.domain.types import (
    Boolean,
    ConfigurationDigest,
    MemoryBytes,
    MetricValue,
    RecordCount,
    RuntimeSeconds,
    SeedValue,
    StandardizedError,
)
from fedcampaign_emhi.emhi.evidence import signed_evidence_factor
from fedcampaign_emhi.evaluation.scalability import (
    resident_set_bytes,
)
from fedcampaign_emhi.evaluation.validation import run_synthetic_module_validation
from fedcampaign_emhi.experiments.calibration import (
    CompositionCandidateObservation,
    CompositionCandidateSeedMetrics,
    FiniteHorizonObservation,
    FiniteHorizonSeedMetrics,
    SignedTheoremObservation,
    emhi_method_settings,
    evaluate_comparator_pure_order_cell,
    evaluate_composition_candidate_seed,
    evaluate_finite_horizon_common_mode_seed,
    evaluate_fitted_pure_order_grid,
)
from fedcampaign_emhi.experiments.execution import (
    ExperimentExecutionResult,
    campaigns_logger,
    experiment_contract,
    fork_multiprocessing_context,
    publish_experiment_run_record,
)
from fedcampaign_emhi.experiments.registry import (
    confirmatory_completeness_within_tolerance,
)
from fedcampaign_emhi.experiments.synthetic import (
    EstimatorFeasibilityObservation,
    HofdEquivalenceObservation,
    PureOrderObservation,
    PureOrderSeedMetrics,
    SelfExplanationObservation,
    SyntheticCellOutcome,
    run_synthetic_cell,
    synthetic_role_seeds,
)
from fedcampaign_emhi.experiments.technical_retry import with_technical_retry
from fedcampaign_emhi.synthetic.generators import validate_synthetic_generators
from fedcampaign_emhi.synthetic.pure_order import enumerate_pure_order_grid
from fedcampaign_emhi.synthetic.self_explanation import (
    analytic_direct_derivative,
    primary_directional_test_passes,
)


def execute_synthetic_module_validation(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    overwrite_policy: OverwritePolicy,
) -> ExperimentExecutionResult:
    experiment_name = ExperimentName.SYNTHETIC_MODULE_VALIDATION
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    staging = layout.roots.outputs_root / "cache" / "staging" #TODO: should be enums not hardcoded strings
    started = perf_counter()
    invariant_criterion = run_synthetic_module_validation(loaded)
    generator_criterion = validate_synthetic_generators(loaded.values)
    repeatability_criterion = run_synthetic_module_validation(loaded)
    repeatability_deviation = abs(
        invariant_criterion.maximum_absolute_identity_error
        - repeatability_criterion.maximum_absolute_identity_error
    )
    deterministic_seed_repeat_agreement = repeatability_criterion == invariant_criterion
    repeatability_tolerance = loaded.values.synthetic_module_validation.repeatability_tolerance
    state = (
        ExperimentState.COMPLETED
        if (
            invariant_criterion.passed
            and generator_criterion.state is ExperimentState.COMPLETED
            and generator_criterion.executed_check_count
            == loaded.values.synthetic_module_validation.expected_generator_check_count
            and deterministic_seed_repeat_agreement
            and repeatability_deviation <= repeatability_tolerance
        )
        else ExperimentState.INVALID
    )
    diagnostic_path = root / "diagnostics" / "scientific" / "synthetic-validation.json" #TODO: should be enums not hardcoded strings
    diagnostic_payload: YamlNode = {
        "state": state.value,
        "invariant_failures": [failure.label for failure in invariant_criterion.failures],
        "generator_failures": list(generator_criterion.failed_checks),
        "executed_fixture_count": len(invariant_criterion.executed_fixture_names),
        "expected_fixture_count": invariant_criterion.expected_fixture_count,
        "executed_fixture_names": [
            fixture.label for fixture in invariant_criterion.executed_fixture_names
        ],
        "maximum_absolute_identity_error": invariant_criterion.maximum_absolute_identity_error,
        "exact_identity_tolerance": invariant_criterion.exact_identity_tolerance,
        "worst_error_to_tolerance_ratio": (
            invariant_criterion.maximum_absolute_identity_error
            / invariant_criterion.exact_identity_tolerance
        ),
        "repeatability_deviation": repeatability_deviation,
        "repeatability_tolerance": repeatability_tolerance,
        "deterministic_seed_repeat_agreement": deterministic_seed_repeat_agreement,
        "expected_negative_fixture_count": generator_criterion.expected_negative_fixture_count,
        "correctly_rejected_negative_fixture_count": (
            generator_criterion.correctly_rejected_negative_fixture_count
        ),
        "executed_generator_check_count": generator_criterion.executed_check_count,
        "expected_generator_check_count": (
            loaded.values.synthetic_module_validation.expected_generator_check_count
        ),
        "bounded_evidence_factor": {
            "signed_positive": signed_evidence_factor(
                1.0, loaded.values.evidence.clip_bound, loaded.values.evidence.bet_lambda
            ),
            "signed_negative": signed_evidence_factor(
                -1.0, loaded.values.evidence.clip_bound, loaded.values.evidence.bet_lambda
            ),
        },
    }
    diagnostic_hash = write_atomic_json(diagnostic_path, diagnostic_payload, staging)
    fingerprint = material_fingerprint(
        synthetic_invariant_boundary_digest(loaded.values),
        (),
    )
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
        peak_rss_bytes=resident_set_bytes(),
        application_payload_bytes=len(diagnostic_path.read_bytes()),
        completion_record=completion,
    )
    cell_path = root / "provenance" / "dependencies" / "cell-validation.json" #TODO: should be enums not hardcoded strings
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


def run_synthetic_cell_with_technical_retry(
    loaded: LoadedScientificConfiguration,
    experiment_name: ExperimentName,
    seed: SeedValue,
    method_name: MethodName | None,
    execution_role: ExecutionRole,
) -> SyntheticCellOutcome:
    return with_technical_retry(
        loaded,
        lambda: run_synthetic_cell(loaded, experiment_name, seed, method_name, execution_role),
    )


@dataclass(frozen=True)
class SyntheticCellExecution:
    state: ExperimentState
    outcome: SyntheticCellOutcome
    finite_horizon_metrics: FiniteHorizonSeedMetrics | None
    composition_metrics: CompositionCandidateSeedMetrics | None
    technical_failure: Boolean
    runtime_seconds: RuntimeSeconds
    peak_rss_bytes: MemoryBytes


_SYNTHETIC_EXECUTION_ADAPTER = TypeAdapter(SyntheticCellExecution)


@dataclass(frozen=True)
class _SyntheticCheckpointPayload:
    experiment_name: ExperimentName
    execution_role: ExecutionRole
    seed: SeedValue
    method_name: MethodName | None
    material_digest: ConfigurationDigest
    execution: SyntheticCellExecution


_CHECKPOINT_PAYLOAD_ADAPTER = TypeAdapter(_SyntheticCheckpointPayload)


def checkpoint_path(
    root: Path, role: ExecutionRole, seed: SeedValue, method_name: MethodName | None
) -> Path:
    method_slug = (
        "coordinate-validation" if method_name is None else method_artifact_stem(method_name)
    )
    return (
        root / "provenance" / "checkpoints" / f"worker-{role.value}-{method_slug}-seed-{seed}.json" #TODO: should be enums not hardcoded strings
    )


def checkpoint_payload(
    loaded: LoadedScientificConfiguration,
    experiment_name: ExperimentName,
    role: ExecutionRole,
    seed: SeedValue,
    method_name: MethodName | None,
    execution: SyntheticCellExecution,
) -> YamlNode:
    return {
        "experiment_name": experiment_name.value,
        "execution_role": role.value,
        "seed": seed,
        "method_name": None if method_name is None else method_name.value,
        "material_digest": loaded.material_digest,
        "execution": cast(
            YamlNode, _SYNTHETIC_EXECUTION_ADAPTER.dump_python(execution, mode="json")
        ),
    }


def load_reusable_checkpoint(
    loaded: LoadedScientificConfiguration,
    experiment_name: ExperimentName,
    role: ExecutionRole,
    seed: SeedValue,
    method_name: MethodName | None,
    root: Path,
) -> SyntheticCellExecution | None:
    path = checkpoint_path(root, role, seed, method_name)
    if not path.is_file():
        return None
    try:
        checkpoint = _CHECKPOINT_PAYLOAD_ADAPTER.validate_python(loads(path.read_bytes()))
        if (
            checkpoint.experiment_name != experiment_name
            or checkpoint.execution_role != role
            or checkpoint.seed != seed
            or checkpoint.method_name != method_name
            or checkpoint.material_digest != loaded.material_digest
        ):
            return None
        execution = checkpoint.execution
        return (
            None
            if execution.technical_failure or execution.state is not ExperimentState.COMPLETED
            else execution
        )
    except ValueError:
        return None


def execute_synthetic_cell_payload(
    loaded: LoadedScientificConfiguration,
    experiment_name: ExperimentName,
    role: ExecutionRole,
    seed: SeedValue,
    method_name: MethodName | None,
    fit_checkpoint_root: Path | None = None,
) -> SyntheticCellExecution:
    started = perf_counter()
    campaigns_logger().info(
        "synthetic_worker_phase experiment=%s role=%s seed=%s method=%s phase=started",
        experiment_name.value,
        role.value,
        seed,
        "coordinate-validation" if method_name is None else method_name.value,
    )
    finite_horizon_metrics: FiniteHorizonSeedMetrics | None = None
    composition_metrics: CompositionCandidateSeedMetrics | None = None
    technical_failure = False
    try:
        outcome = run_synthetic_cell_with_technical_retry(
            loaded, experiment_name, seed, method_name, role
        )
        campaigns_logger().info(
            "synthetic_worker_phase experiment=%s role=%s seed=%s method=%s phase=primary_check_completed",
            experiment_name.value,
            role.value,
            seed,
            "coordinate-validation" if method_name is None else method_name.value,
        )
        if (
            experiment_name is ExperimentName.PURE_ORDER_SEPARATION_VALIDATION
            and method_name is not None
            and emhi_method_settings(method_name) is not None
        ):
            primary = loaded.values.experiments.pure_order_separation_validation.primary_condition
            fitted_grid = evaluate_fitted_pure_order_grid(loaded.values, method_name, seed)
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
            grid_complete = all(fitted.artifact_path_complete for _cell, fitted in fitted_grid)
            if grid_complete:
                evidence = dict(cast(Mapping[str, YamlNode], outcome.evidence))
                evidence["exact_exclusion_artifact_grid_complete"] = grid_complete
                evidence["implementation_state"] = "fitted_emhi_artifact_grid"
                evidence["fitted_emhi_scores"] = [
                    {
                        "generator": cell.generator.value,
                        "effect": cell.effect,
                        "target_order": cell.target_order,
                        "maximum_proper_subset_standardized_drift": fitted.metrics.maximum_proper_subset_standardized_drift,
                        "target_order_standardized_drift": fitted.metrics.target_order_standardized_drift,
                    }
                    for cell, fitted in fitted_grid
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
                        if primary_fitted is not None and primary_fitted.artifact_path_complete
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
                (cell, metrics) for cell, metrics in comparator_grid if metrics is not None
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
                        "target_order": cell.target_order,
                        "target_order_standardized_drift": metrics.target_order_standardized_drift,
                    }
                    for cell, metrics in comparator_completed
                ]
                evidence["native_comparator_grid"] = {
                    "native_target_order": native_order if native_order is not None else None,
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
            campaigns_logger().info(
                "synthetic_worker_phase experiment=%s role=%s seed=%s phase=finite_horizon_started",
                experiment_name.value,
                role.value,
                seed,
            )
            finite_horizon = evaluate_finite_horizon_common_mode_seed(
                loaded.values,
                seed,
                None
                if fit_checkpoint_root is None
                else fit_checkpoint_root / "finite-horizon-emhi",
            )
            finite_horizon_metrics = finite_horizon.metrics
            campaigns_logger().info(
                "synthetic_worker_phase experiment=%s role=%s seed=%s phase=finite_horizon_completed",
                experiment_name.value,
                role.value,
                seed,
            )
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
        if (
            experiment_name is ExperimentName.STRONG_COMPARATOR_COMPOSITION_CHALLENGE
            and role is ExecutionRole.DEVELOPMENT
            and method_name is not None
            and not outcome.failed_checks
        ):
            composition_metrics = evaluate_composition_candidate_seed(
                loaded.values, method_name, seed
            )
            evidence = dict(cast(Mapping[str, YamlNode], outcome.evidence))
            evidence["composition_calibration"] = {
                "calibrated_threshold": composition_metrics.calibrated_threshold,
                "calibration_horizon_count": composition_metrics.calibration_horizon_count,
                "heldout_horizon_count": composition_metrics.heldout_horizon_count,
                "heldout_false_stop_count": composition_metrics.heldout_false_stop_count,
                "scoring_runtime_seconds": composition_metrics.scoring_runtime_seconds,
                "operating_point_available": composition_metrics.calibrated_threshold is not None,
            }
            outcome = replace(outcome, evidence=evidence)
    except (ArithmeticError, ValueError) as error:
        outcome = SyntheticCellOutcome((str(error),), None)
    except (OSError, MemoryError) as error:
        outcome = SyntheticCellOutcome((str(error),), None)
        technical_failure = True
    state = (
        ExperimentState.FAILED
        if technical_failure
        else ExperimentState.COMPLETED
        if not outcome.failed_checks
        else ExperimentState.INVALID
    )
    return SyntheticCellExecution(
        state,
        outcome,
        finite_horizon_metrics,
        composition_metrics,
        technical_failure,
        perf_counter() - started,
        resident_set_bytes(),
    )


def execute_synthetic_worker_task(
    task: tuple[
        LoadedScientificConfiguration,
        ExperimentName,
        ExecutionRole,
        SeedValue,
        MethodName | None,
        Path | None,
    ],
) -> SyntheticCellExecution:
    loaded, experiment_name, role, seed, method_name, fit_checkpoint_root = task
    return execute_synthetic_cell_payload(
        loaded, experiment_name, role, seed, method_name, fit_checkpoint_root
    )


def _synthetic_dispatch_method(
    experiment_name: ExperimentName, method_name: MethodName | None
) -> MethodName | None:
    if (
        experiment_name is ExperimentName.EXCLUSION_MATCHED_HOFD_EQUIVALENCE
        and method_name is MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD
    ):
        return MethodName.FULL_FEDCAMPAIGN_EMHI
    return method_name


def execute_synthetic_experiment(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    overwrite_policy: OverwritePolicy,
) -> ExperimentExecutionResult:
    contract = experiment_contract(loaded.values, experiment_name)
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    staging = layout.roots.outputs_root / "cache" / "staging" #TODO: should be enums not hardcoded strings
    methods: tuple[MethodName | None, ...] = contract.methods or (None,)
    cells: list[tuple[ExecutionRole, SeedValue, MethodName | None]] = []
    for role in contract.execution_roles:
        for seed in synthetic_role_seeds(loaded, role):
            for method_name in methods:
                cells.append((role, seed, method_name))
    dispatched_cells: UserDict[
        tuple[ExecutionRole, SeedValue, MethodName | None], tuple[RecordCount, ...]
    ] = UserDict()
    for cell_index, (role, seed, method_name) in enumerate(cells):
        dispatch = (role, seed, _synthetic_dispatch_method(experiment_name, method_name))
        dispatched_cells[dispatch] = (*dispatched_cells.get(dispatch, ()), cell_index)
    dispatched_order: list[tuple[ExecutionRole, SeedValue, MethodName | None]] = list(
        dispatched_cells
    )
    reusable: list[
        tuple[tuple[ExecutionRole, SeedValue, MethodName | None], SyntheticCellExecution]
    ] = []
    pending_dispatches: list[tuple[ExecutionRole, SeedValue, MethodName | None]] = []
    for dispatch in dispatched_order:
        role, seed, method_name = dispatch
        checkpoint = (
            None
            if overwrite_policy is OverwritePolicy.OVERWRITE
            else load_reusable_checkpoint(loaded, experiment_name, role, seed, method_name, root)
        )
        if checkpoint is None:
            pending_dispatches.append(dispatch)
        else:
            reusable.append((dispatch, checkpoint))
    worker_count = max(
        1,
        min(
            len(pending_dispatches),
            os.cpu_count() or 1,
            loaded.values.runtime.synthetic_concurrent_experiment_cells,
        ),
    )
    tasks = tuple(
        (
            loaded,
            experiment_name,
            dispatch_role,
            dispatch_seed,
            dispatch_method,
            root,
        )
        for dispatch_role, dispatch_seed, dispatch_method in pending_dispatches
    )
    campaigns_logger().info(
        "experiment_cells experiment=%s cell_count=%d dispatched_count=%d reused_count=%d worker_count=%d",
        experiment_name.value,
        len(cells),
        len(pending_dispatches),
        len(reusable),
        worker_count,
    )
    self_explanation_slots: list[list[SelfExplanationObservation]] = [[] for _ in cells]
    pure_order_slots: list[list[PureOrderObservation]] = [[] for _ in cells]
    signed_theorem_slots: list[list[SignedTheoremObservation]] = [[] for _ in cells]
    finite_horizon_slots: list[list[FiniteHorizonObservation]] = [[] for _ in cells]
    estimator_feasibility_slots: list[list[EstimatorFeasibilityObservation]] = [[] for _ in cells]
    composition_slots: list[list[CompositionCandidateObservation]] = [[] for _ in cells]
    hofd_slots: list[list[HofdEquivalenceObservation]] = [[] for _ in cells]
    completed = 0
    invalid = 0

    def executions() -> Iterator[
        tuple[tuple[ExecutionRole, SeedValue, MethodName | None], SyntheticCellExecution]
    ]:
        yield from reusable
        if not tasks:
            return
        fork_context = fork_multiprocessing_context()
        with ProcessPoolExecutor(max_workers=worker_count, mp_context=fork_context) as pool:
            pending = iter(zip(tasks, pending_dispatches, strict=True))
            futures: MutableMapping[
                Future[SyntheticCellExecution],
                tuple[ExecutionRole, SeedValue, MethodName | None],
            ] = {}

            def submit_one() -> bool:
                try:
                    task, dispatch = next(pending)
                except StopIteration:
                    return False
                futures[pool.submit(execute_synthetic_worker_task, task)] = dispatch
                return True

            for _index in range(min(len(tasks), worker_count * 2)):
                submit_one()
            started = perf_counter()
            finished_count = 0
            while futures:
                finished, _pending = wait(
                    futures,
                    timeout=loaded.values.runtime.progress_log_interval_seconds,
                    return_when=FIRST_COMPLETED,
                )
                if not finished:
                    campaigns_logger().info(
                        "experiment_progress experiment=%s finished_dispatches=%d "
                        "remaining_dispatches=%d elapsed_seconds=%.3f",
                        experiment_name.value,
                        finished_count,
                        len(tasks) - finished_count,
                        perf_counter() - started,
                    )
                    continue
                for future in finished:
                    dispatch = futures.pop(future)
                    finished_count += 1
                    submit_one()
                    yield dispatch, future.result()

    for (role, seed, method_name), execution in executions():
        state = execution.state
        for cell_index in dispatched_cells[(role, seed, method_name)]:
            _role, _seed, cell_method = cells[cell_index]
            method_slug = (
                "coordinate-validation"
                if cell_method is None
                else method_artifact_stem(cell_method)
            )
            diagnostic_path = (
                root
                / "diagnostics" #TODO: should be enums not hardcoded strings
                / "scientific" #TODO: should be enums not hardcoded strings
                / _role.value
                / method_slug
                / f"seed-{_seed}.json" #TODO: should be enums not hardcoded strings
            )
            diagnostic_payload: YamlNode = {
                "experiment_name": experiment_name.value,
                "execution_role": _role.value,
                "seed": _seed,
                "method_name": None if cell_method is None else cell_method.value,
                "state": state.value,
                "failed_checks": list(execution.outcome.failed_checks),
                "method_score": execution.outcome.method_score,
                "evidence": execution.outcome.evidence,
            }
            diagnostic_hash = write_atomic_json(diagnostic_path, diagnostic_payload, staging)
            cell_checkpoint_path = checkpoint_path(root, _role, _seed, cell_method)
            checkpoint_hash = write_atomic_json(
                cell_checkpoint_path,
                checkpoint_payload(
                    loaded,
                    experiment_name,
                    _role,
                    _seed,
                    cell_method,
                    execution,
                ),
                staging,
            )
            campaigns_logger().info(
                "synthetic_checkpoint_published experiment=%s role=%s seed=%s method=%s",
                experiment_name.value,
                _role.value,
                _seed,
                "coordinate-validation" if cell_method is None else cell_method.value,
            )
            outcome = execution.outcome
            if state is ExperimentState.COMPLETED and outcome.self_explanation_metrics is not None:
                self_explanation_slots[cell_index].append(
                    SelfExplanationObservation(
                        execution_role=_role,
                        seed=_seed,
                        metric=outcome.self_explanation_metrics,
                        diagnostic_path=diagnostic_path,
                    )
                )
            if state is ExperimentState.COMPLETED and outcome.pure_order_metrics is not None:
                pure_order_slots[cell_index].append(
                    PureOrderObservation(
                        execution_role=_role,
                        seed=_seed,
                        metric=outcome.pure_order_metrics,
                        diagnostic_path=diagnostic_path,
                    )
                )
            if state is ExperimentState.COMPLETED and outcome.signed_theorem_metrics is not None:
                signed_theorem_slots[cell_index].append(
                    SignedTheoremObservation(
                        execution_role=_role,
                        seed=_seed,
                        metric=outcome.signed_theorem_metrics,
                        diagnostic_path=diagnostic_path,
                    )
                )
            if state is ExperimentState.COMPLETED and execution.finite_horizon_metrics is not None:
                finite_horizon_slots[cell_index].append(
                    FiniteHorizonObservation(
                        execution_role=_role,
                        seed=_seed,
                        metric=execution.finite_horizon_metrics,
                        diagnostic_path=diagnostic_path,
                    )
                )
            if (
                state is ExperimentState.COMPLETED
                and outcome.estimator_feasibility_metrics is not None
            ):
                estimator_feasibility_slots[cell_index].append(
                    EstimatorFeasibilityObservation(
                        execution_role=_role,
                        seed=_seed,
                        metric=outcome.estimator_feasibility_metrics,
                        diagnostic_path=diagnostic_path,
                    )
                )
            if state is ExperimentState.COMPLETED and outcome.hofd_metrics is not None:
                hofd_slots[cell_index].append(
                    HofdEquivalenceObservation(
                        execution_role=_role,
                        seed=_seed,
                        metric=outcome.hofd_metrics,
                        diagnostic_path=diagnostic_path,
                    )
                )
            if (
                state is ExperimentState.COMPLETED
                and execution.composition_metrics is not None
                and cell_method is not None
            ):
                evidence = cast(Mapping[str, YamlNode], outcome.evidence)
                composition_slots[cell_index].append(
                    CompositionCandidateObservation(
                        method_name=cell_method,
                        seed=_seed,
                        standardized_target_order_error=cast(
                            StandardizedError, evidence["standardized_target_order_error"]
                        ),
                        metric=execution.composition_metrics,
                        diagnostic_path=diagnostic_path,
                    )
                )
            fingerprint = material_fingerprint(
                synthetic_cell_boundary_digest(loaded.values),
                (payload_digest(cast(YamlNode, {"seed": _seed, "method": method_slug})),),
            )
            completion = CompletionRecord(
                state=state,
                mandatory_output_paths=(
                    diagnostic_path.relative_to(repository).as_posix(),
                    cell_checkpoint_path.relative_to(repository).as_posix(),
                ),
                mandatory_output_hashes=(diagnostic_hash, checkpoint_hash),
            )
            cell = ScientificCellRecord(
                experiment_name=experiment_name,
                execution_role=_role,
                semantic_cell_path=f"{_role.value}/{method_slug}/seed-{_seed}",
                method_name=cell_method,
                seed=_seed,
                state=state,
                material_digest=loaded.material_digest,
                selected_client_ids=(),
                upstream_artifact_ids=(),
                dependency_fingerprint=fingerprint,
                runtime_seconds=execution.runtime_seconds,
                peak_rss_bytes=execution.peak_rss_bytes,
                application_payload_bytes=len(diagnostic_path.read_bytes()),
                completion_record=completion,
            )
            cell_path = (
                root
                / "provenance" #TODO: should be enums not hardcoded strings
                / "dependencies" #TODO: should be enums not hardcoded strings
                / f"cell-{_role.value}-{method_slug}-seed-{_seed}.json" #TODO: should be enums not hardcoded strings
            )
            write_atomic_json(cell_path, cast(YamlNode, cell.model_dump(mode="json")), staging)
            if state is ExperimentState.COMPLETED:
                completed += 1
            else:
                invalid += 1
            campaigns_logger().info(
                "cell_completed experiment=%s role=%s seed=%s method=%s state=%s"
                " elapsed_seconds=%.3f completed_cells=%d invalid_cells=%d total_cells=%d",
                experiment_name.value,
                _role.value,
                _seed,
                "coordinate-validation" if cell_method is None else cell_method.value,
                state.value,
                execution.runtime_seconds,
                completed,
                invalid,
                len(cells),
            )
    self_explanation_observations = tuple(
        observation for slot in self_explanation_slots for observation in slot
    )
    pure_order_observations = tuple(
        observation for slot in pure_order_slots for observation in slot
    )
    signed_theorem_observations = tuple(
        observation for slot in signed_theorem_slots for observation in slot
    )
    finite_horizon_observations = tuple(
        observation for slot in finite_horizon_slots for observation in slot
    )
    estimator_feasibility_observations = tuple(
        observation for slot in estimator_feasibility_slots for observation in slot
    )
    composition_observations = tuple(
        observation for slot in composition_slots for observation in slot
    )
    hofd_observations = tuple(observation for slot in hofd_slots for observation in slot)
    if experiment_name is ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION:
        materialize_self_explanation_statistics(loaded, repository, self_explanation_observations)
    if experiment_name is ExperimentName.PURE_ORDER_SEPARATION_VALIDATION:
        materialize_pure_order_statistics(loaded, repository, pure_order_observations)
    if experiment_name is ExperimentName.SEQUENTIAL_EVIDENCE_VALIDATION:
        materialize_signed_theorem_statistics(loaded, repository, signed_theorem_observations)
        materialize_finite_horizon_statistics(loaded, repository, finite_horizon_observations)
    if experiment_name is ExperimentName.ESTIMATOR_SUPPORT_AND_CONTEXT_FEASIBILITY:
        materialize_estimator_feasibility_statistics(
            loaded, repository, estimator_feasibility_observations
        )
    if experiment_name is ExperimentName.STRONG_COMPARATOR_COMPOSITION_CHALLENGE:
        materialize_strong_comparator_composition_selection(
            loaded, repository, composition_observations
        )
    if experiment_name is ExperimentName.EXCLUSION_MATCHED_HOFD_EQUIVALENCE:
        materialize_hofd_equivalence_statistics(loaded, repository, hofd_observations)
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
    observed_seeds = tuple(observation.seed for observation in confirmatory)
    if not confirmatory_completeness_within_tolerance(loaded, expected, observed_seeds):
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
    derivatives = tuple(
        observation.metric.primary_exact_nuisance_derivative for observation in confirmatory
    )
    interval_of_derivatives = paired_mean_bca_interval(
        derivatives,
        loaded.values.statistics.confidence_level,
        loaded.values.statistics.bootstrap_replicates,
        loaded.values.randomness.statistical_analysis_base_seed,
    )
    direct = analytic_direct_derivative()
    fraction = loaded.values.materiality.self_explanation.exact_exclusion_nuisance_derivative_equivalence_fraction_of_direct
    equivalence_margin = fraction * abs(direct)
    equivalence_established = interval_establishes_equivalence(
        interval_of_derivatives[0],
        interval_of_derivatives[1],
        -equivalence_margin,
        equivalence_margin,
    )
    attenuation_shift = hodges_lehmann_shift(values)
    layout = build_artifact_layout(loaded, repository)
    source_paths = tuple(observation.diagnostic_path for observation in confirmatory)
    source_digests = tuple(file_sha256(path) for path in source_paths)
    source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
    payload: YamlNode = {
        "experiment_name": ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION.value,
        "hypothesis_identifier": PrimaryHolmHypothesis.SELF_EXPLANATION_MATERIAL_ATTENUATION.value,
        "metric_name": "primary_attenuation_contrast", #TODO: should be enums not hardcoded strings
        "method_name": "Exact Complement Exclusion", #TODO: should be enums not hardcoded strings
        "independent_unit_count": len(values),
        "estimate": sum(values) / len(values),
        "raw_p_value": raw_p_value,
        "confidence_level": loaded.values.statistics.confidence_level,
        "confidence_lower": interval[0],
        "confidence_upper": interval[1],
        "hodges_lehmann_shift": attenuation_shift,
        "equivalence_established": equivalence_established,
        "source_result_ids": list(source_ids),
    }
    record = StatisticalRecord(
        hypothesis_identifier=PrimaryHolmHypothesis.SELF_EXPLANATION_MATERIAL_ATTENUATION.value,
        metric_name="primary_attenuation_contrast",
        method_name="Exact Complement Exclusion",
        independent_unit_count=len(values),
        estimate=sum(values) / len(values),
        raw_p_value=raw_p_value,
        adjusted_p_value=None,
        confidence_level=loaded.values.statistics.confidence_level,
        confidence_lower=interval[0],
        confidence_upper=interval[1],
        hodges_lehmann_shift=attenuation_shift,
        equivalence_established=equivalence_established,
        meets_threshold=primary_directional_test_passes(
            raw_p_value, loaded.values.statistics.nominal_significance_alpha
        ),
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values),
            source_digests,
        ),
        content_digest=payload_digest(payload),
    )
    path = (
        layout.experiment_outputs_root(ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION)
        / "statistics" #TODO: should be enums not hardcoded strings
        / "tests" #TODO: should be enums not hardcoded strings
        / "self-explanation-material-attenuation.json" #TODO: should be enums not hardcoded strings
    )
    staging = layout.roots.outputs_root / "cache" / "staging" #TODO: should be enums not hardcoded strings
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
    observed_seeds = tuple(observation.seed for observation in confirmatory)
    if not confirmatory_completeness_within_tolerance(loaded, expected, observed_seeds):
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
    hypothesis_identifier = PrimaryHolmHypothesis.PURE_ORDER_TARGET_DRIFT.value
    payload: YamlNode = {
        "experiment_name": ExperimentName.PURE_ORDER_SEPARATION_VALIDATION.value,
        "hypothesis_identifier": hypothesis_identifier,
        "metric_name": "target_order_standardized_drift", #TODO: should be enums not hardcoded strings
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
        hypothesis_identifier=hypothesis_identifier,
        metric_name="target_order_standardized_drift",
        method_name=MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        independent_unit_count=len(values),
        estimate=sum(values) / len(values),
        raw_p_value=raw_p_value,
        adjusted_p_value=None,
        confidence_level=loaded.values.statistics.confidence_level,
        confidence_lower=interval[0],
        confidence_upper=interval[1],
        meets_threshold=raw_p_value < loaded.values.statistics.nominal_significance_alpha,
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values),
            source_digests,
        ),
        content_digest=payload_digest(payload),
    )
    path = (
        layout.experiment_outputs_root(ExperimentName.PURE_ORDER_SEPARATION_VALIDATION)
        / "statistics" #TODO: should be enums not hardcoded strings
        / "tests" #TODO: should be enums not hardcoded strings
        / "pure-order-target-drift.json" #TODO: should be enums not hardcoded strings
    )
    staging = layout.roots.outputs_root / "cache" / "staging" #TODO: should be enums not hardcoded strings
    write_atomic_json(path, cast(YamlNode, record.model_dump(mode="json")), staging)
    return path


def materialize_hofd_equivalence_statistics(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    observations: tuple[HofdEquivalenceObservation, ...],
) -> Path | None:
    confirmatory = tuple(
        observation
        for observation in observations
        if observation.execution_role is ExecutionRole.CONFIRMATORY
    )
    expected = loaded.values.randomness.synthetic_confirmatory_roots
    observed_seeds = tuple(observation.seed for observation in confirmatory)
    if not confirmatory_completeness_within_tolerance(loaded, expected, observed_seeds):
        return None
    materiality = loaded.values.materiality.hofd_equivalence
    interval = materiality.stopping_time_difference_interval_epochs
    confidence_level = loaded.values.statistics.confidence_level
    replicates = loaded.values.statistics.bootstrap_replicates
    analysis_seed = loaded.values.randomness.statistical_analysis_base_seed
    conditions: list[YamlNode] = []
    nrmse_estimates: list[MetricValue] = []
    all_supported = True
    primary_supports = (
        loaded.values.experiments.exclusion_matched_hofd_equivalence.primary_support_levels
    )
    for order in CoalitionOrder:
        if order > loaded.values.study.maximum_coalition_order:
            continue
        for support in primary_supports:
            matched = tuple(
                metric
                for observation in confirmatory
                for metric in observation.metric.conditions
                if metric.coalition_order is order and metric.support_per_context == support
            )
            if len(matched) != len(confirmatory):
                all_supported = False
                conditions.append(
                    {
                        "coalition_order": order,
                        "support_per_context": support,
                        "meets_threshold": False,
                    }
                )
                continue
            nrmse_values = tuple(metric.atom_nrmse for metric in matched)
            cosine_values = tuple(metric.atom_cosine_similarity for metric in matched)
            nrmse_interval = paired_mean_bca_interval(
                nrmse_values, confidence_level, replicates, analysis_seed
            )
            stop_values = tuple(
                metric.stopping_time_difference
                for metric in matched
                if metric.pfa_prerequisite_passes and metric.stopping_time_difference is not None
            )
            pfa_ok = all(metric.pfa_prerequisite_passes for metric in matched)
            stop_interval = (
                paired_mean_bca_interval(stop_values, confidence_level, replicates, analysis_seed)
                if stop_values and pfa_ok
                else None
            )
            nrmse_estimate = sum(nrmse_values) / len(nrmse_values)
            nrmse_estimates.append(nrmse_estimate)
            nrmse_ok = nrmse_equivalence_criterion(
                nrmse_interval[1], materiality.atom_nrmse_upper_margin
            )
            cosine_ok = cosine_equivalence_criterion(
                sum(cosine_values) / len(cosine_values),
                materiality.minimum_cosine_similarity,
            )
            stop_ok = stop_interval is not None and stopping_time_equivalence_criterion(
                stop_interval[0],
                stop_interval[1],
                interval[0],
                interval[1],
            )
            supported = nrmse_ok and cosine_ok and pfa_ok and stop_ok
            all_supported = all_supported and supported
            conditions.append(
                {
                    "coalition_order": order,
                    "support_per_context": support,
                    "nrmse_estimate": nrmse_estimate,
                    "nrmse_confidence_lower": nrmse_interval[0],
                    "nrmse_confidence_upper": nrmse_interval[1],
                    "mean_cosine_similarity": sum(cosine_values) / len(cosine_values),
                    "pfa_prerequisite_passes": pfa_ok,
                    "stopping_time_difference_estimate": (
                        None if not stop_values else sum(stop_values) / len(stop_values)
                    ),
                    "stopping_time_confidence_lower": (
                        None if stop_interval is None else stop_interval[0]
                    ),
                    "stopping_time_confidence_upper": (
                        None if stop_interval is None else stop_interval[1]
                    ),
                    "meets_threshold": supported,
                }
            )
    layout = build_artifact_layout(loaded, repository)
    source_paths = tuple(observation.diagnostic_path for observation in confirmatory)
    source_digests = tuple(file_sha256(path) for path in source_paths)
    source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
    payload: YamlNode = {
        "experiment_name": ExperimentName.EXCLUSION_MATCHED_HOFD_EQUIVALENCE.value,
        "hypothesis_identifier": "Exclusion-Matched HOFD Equivalence", #TODO: should be enums not hardcoded strings
        "metric_name": "atom_nrmse_cosine_stopping_time", #TODO: should be enums not hardcoded strings
        "method_name": MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD.value,
        "independent_unit_count": len(confirmatory),
        "confidence_level": confidence_level,
        "conditions": conditions,
        "source_result_ids": list(source_ids),
    }
    record = StatisticalRecord(
        hypothesis_identifier="Exclusion-Matched HOFD Equivalence",
        metric_name="atom_nrmse_cosine_stopping_time",
        method_name=MethodName.EXCLUSION_MATCHED_CONDITIONAL_HOFD.value,
        independent_unit_count=len(confirmatory),
        estimate=(sum(nrmse_estimates) / len(nrmse_estimates) if nrmse_estimates else 0.0),
        raw_p_value=None,
        adjusted_p_value=None,
        confidence_level=confidence_level,
        confidence_lower=None,
        confidence_upper=None,
        meets_threshold=all_supported,
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values),
            source_digests,
        ),
        content_digest=payload_digest(payload),
    )
    path = (
        layout.experiment_outputs_root(ExperimentName.EXCLUSION_MATCHED_HOFD_EQUIVALENCE)
        / "statistics" #TODO: should be enums not hardcoded strings
        / "tests" #TODO: should be enums not hardcoded strings
        / "exclusion-matched-hofd-equivalence.json" #TODO: should be enums not hardcoded strings
    )
    staging = layout.roots.outputs_root / "cache" / "staging" #TODO: should be enums not hardcoded strings
    write_atomic_json(path, cast(YamlNode, record.model_dump(mode="json")), staging)
    return path


def materialize_strong_comparator_composition_selection(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    observations: tuple[CompositionCandidateObservation, ...],
) -> Path | None:
    expected_seeds = loaded.values.randomness.synthetic_development_roots
    candidates: list[CompositionCandidateResult] = []
    source_paths: list[Path] = []
    for method_name in loaded.values.experiments.strong_comparator_composition_challenge.candidates:
        seed_observations = tuple(
            observation for observation in observations if observation.method_name is method_name
        )
        if tuple(observation.seed for observation in seed_observations) != expected_seeds:
            continue
        source_paths.extend(observation.diagnostic_path for observation in seed_observations)
        candidates.append(
            CompositionCandidateResult(
                method_name=method_name,
                invariants_pass=True,
                calibration_succeeded=all(
                    observation.metric.calibrated_threshold is not None
                    for observation in seed_observations
                ),
                heldout_false_stops=sum(
                    observation.metric.heldout_false_stop_count for observation in seed_observations
                ),
                heldout_horizons=sum(
                    observation.metric.heldout_horizon_count for observation in seed_observations
                ),
                mean_standardized_error=mean_standardized_error(
                    tuple(
                        observation.standardized_target_order_error
                        for observation in seed_observations
                    )
                ),
                median_runtime_seconds=median_runtime_seconds(
                    tuple(
                        observation.metric.scoring_runtime_seconds
                        for observation in seed_observations
                    )
                ),
            )
        )
    if not candidates:
        return None
    selection = loaded.values.experiments.strong_comparator_composition_challenge
    finite_horizon = loaded.values.evidence.calibrated_finite_horizon
    inputs = CompositionSelectionInputs(
        reference_theta=loaded.values.generators.pure_polynomial.primary_reference_theta,
        error_tie_tolerance=selection.error_tie_tolerance_standardized_units,
        runtime_tie_tolerance=selection.runtime_tie_tolerance_seconds,
        calibration_horizons_per_seed=(
            loaded.values.synthetic.sample_sizes.finite_horizon_calibration_horizons_per_seed
        ),
        heldout_null_horizons_per_seed=(
            loaded.values.synthetic.sample_sizes.finite_horizon_heldout_null_horizons_per_seed
        ),
        timed_scoring_rows=(
            loaded.values.synthetic.sample_sizes.pure_order_independent_evaluation_samples_per_condition_seed
        ),
        artifact_filename=selection.artifact_filename,
    )
    source_digests = tuple(file_sha256(path) for path in source_paths)
    try:
        record = build_composition_selection_record(
            tuple(candidates),
            inputs,
            finite_horizon.calibration_confidence,
            finite_horizon.target_pfa,
            evidence_export_boundary_digest(loaded.values),
            source_digests,
        )
    except ValueError:
        return None
    layout = build_artifact_layout(loaded, repository)
    staging = layout.roots.outputs_root / "cache" / "staging" #TODO: should be enums not hardcoded strings
    path = (
        layout.experiment_outputs_root(ExperimentName.STRONG_COMPARATOR_COMPOSITION_CHALLENGE)
        / "artifacts" #TODO: should be enums not hardcoded strings
        / "derived" #TODO: should be enums not hardcoded strings
        / selection.artifact_filename
    )
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
    observed_seeds = tuple(observation.seed for observation in confirmatory)
    if not confirmatory_completeness_within_tolerance(loaded, expected, observed_seeds):
        return None
    metrics = tuple(observation.metric.primary for observation in confirmatory)
    failure_count = sum(metric.numerical_failure for metric in metrics)
    failure_rate = failure_count / len(metrics)
    materiality = loaded.values.materiality
    meets_threshold = (
        sum(metric.context_coverage for metric in metrics) / len(metrics)
        >= materiality.order_three_estimator.minimum_mean_context_coverage
        and sum(metric.projection_nrmse for metric in metrics) / len(metrics)
        <= materiality.order_three_estimator.maximum_mean_projection_nrmse
        and sum(metric.standardized_null_bias for metric in metrics) / len(metrics)
        <= materiality.order_three_estimator.maximum_mean_standardized_null_bias
        and failure_rate <= materiality.maximum_pooled_numerical_failure_rate
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
        "meets_threshold": meets_threshold,
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
        meets_threshold=meets_threshold,
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values),
            source_digests,
        ),
        content_digest=payload_digest(payload),
    )
    path = (
        layout.experiment_outputs_root(ExperimentName.ESTIMATOR_SUPPORT_AND_CONTEXT_FEASIBILITY)
        / "statistics" #TODO: should be enums not hardcoded strings
        / "tests" #TODO: should be enums not hardcoded strings
        / "estimator-order-three-feasibility.json" #TODO: should be enums not hardcoded strings
    )
    staging = layout.roots.outputs_root / "cache" / "staging" #TODO: should be enums not hardcoded strings
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
    observed_seeds = tuple(observation.seed for observation in confirmatory)
    if not confirmatory_completeness_within_tolerance(loaded, expected, observed_seeds):
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
        "hypothesis_identifier": "Signed-Theorem Restricted ARL", #TODO: should be enums not hardcoded strings
        "metric_name": "restricted_arl", #TODO: should be enums not hardcoded strings
        "method_name": "Signed-Theorem Sequential Route", #TODO: should be enums not hardcoded strings
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
        meets_threshold=lower >= threshold,
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values),
            source_digests,
        ),
        content_digest=payload_digest(payload),
    )
    path = (
        layout.experiment_outputs_root(ExperimentName.SEQUENTIAL_EVIDENCE_VALIDATION)
        / "statistics" #TODO: should be enums not hardcoded strings
        / "tests" #TODO: should be enums not hardcoded strings
        / "signed-theorem-restricted-arl.json" #TODO: should be enums not hardcoded strings
    )
    staging = layout.roots.outputs_root / "cache" / "staging" #TODO: should be enums not hardcoded strings
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
    observed_seeds = tuple(observation.seed for observation in confirmatory)
    if not confirmatory_completeness_within_tolerance(loaded, expected, observed_seeds):
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
    meets_threshold = (
        unavailable_count == 0 and maximum_upper is not None and maximum_upper <= target
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
        "meets_threshold": meets_threshold,
        "source_result_ids": list(source_ids),
    }
    record = FiniteHorizonAggregationRecord(
        experiment_name=ExperimentName.SEQUENTIAL_EVIDENCE_VALIDATION,
        independent_unit_count=len(confirmatory),
        operating_point_unavailable_count=unavailable_count,
        target_pfa=target,
        maximum_heldout_upper_pfa=maximum_upper,
        meets_threshold=meets_threshold,
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values),
            source_digests,
        ),
        content_digest=payload_digest(payload),
    )
    path = (
        layout.experiment_outputs_root(ExperimentName.SEQUENTIAL_EVIDENCE_VALIDATION)
        / "statistics" #TODO: should be enums not hardcoded strings
        / "tests" #TODO: should be enums not hardcoded strings
        / "calibrated-finite-horizon-pfa.json" #TODO: should be enums not hardcoded strings
    )
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging", #TODO: should be enums not hardcoded strings
    )
    return path
