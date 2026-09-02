import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from functools import partial
from math import log
from pathlib import Path
from time import perf_counter
from typing import cast

from fedcampaign_emhi.analysis.results import (
    SECONDARY_HOLM_STATISTICS,
    build_seed_summary,
    paired_seed_differences,
)
from fedcampaign_emhi.analysis.statistics import (
    exact_sign_flip_means,
    hodges_lehmann_shift,
    holm_adjusted_p_values,
    interval_establishes_equivalence,
    mean_bca_one_sided_lower_bound,
    one_sided_synthetic_sign_flip_p_value,
    paired_mean_bca_interval,
    sign_flip_p_value,
)
from fedcampaign_emhi.artifacts.provenance import (
    calibration_threshold_boundary_digest,
    campaign_evaluation_boundary_digest,
    evidence_export_boundary_digest,
    material_fingerprint,
    nuisance_context_boundary_digest,
    statistical_analysis_boundary_digest,
    synthetic_cell_boundary_digest,
    synthetic_invariant_boundary_digest,
)
from fedcampaign_emhi.artifacts.records import (
    BenignCommonModePositivePowerMeasurementRecord,
    BenignHorizonRecord,
    BenignPartitionRecord,
    CampaignRegistryRecord,
    ClientDetectorScoreStream,
    ClientFeatureScalerRecord,
    CompletionRecord,
    ContextEstimatorSensitivityCellRecord,
    ContextEstimatorSensitivityMetrics,
    CountStressDiagnosticRecord,
    DatasetSplitRecord,
    DetectorScoreArtifactRecord,
    EMHIFitArtifactRecord,
    EstimatorFeasibilityAggregationRecord,
    ExperimentRunRecord,
    FiniteHorizonAggregationRecord,
    FullMethodSupportRecord,
    MarginalRankArtifactRecord,
    PreparedDatasetRecord,
    ScientificCellRecord,
    SeedSummaryRecord,
    StatisticalRecord,
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
from fedcampaign_emhi.comparators.contracts import (
    ComparatorMethodContract,
    comparator_method_contracts,
    native_target_order,
)
from fedcampaign_emhi.comparators.fusion import (
    CompositionCandidateResult,
    CompositionSelectionInputs,
    build_composition_selection_record,
    mean_standardized_error,
    median_runtime_seconds,
)
from fedcampaign_emhi.comparators.runtime import (
    resolve_comparator_scoring_method,
    score_comparator_ranks,
    validate_comparator_runtime_contracts,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.datasets.preprocessing import apply_robust_scaler
from fedcampaign_emhi.detection import (
    assign_detector_families,
    build_detector_score_artifact,
    detector_seed,
    score_client,
)
from fedcampaign_emhi.domain.enums import (
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
    BasisSize,
    BenignHorizon,
    Boolean,
    CellCount,
    ComponentName,
    ConfigurationDigest,
    ContextCoverage,
    CusumState,
    DetectorScore,
    EpochIndexValue,
    FalseAlarmRate,
    FeatureValue,
    MaterialDependencyFingerprint,
    MetricRate,
    MetricValue,
    OdiIndicator,
    OdiRateAdvantage,
    OperationalLeadEpochs,
    Probability,
    RankValue,
    RecordCount,
    RelativePath,
    RidgePenalty,
    RobustnessCountMultiplier,
    RobustScaler,
    RuntimeSeconds,
    SeedValue,
    StandardizedError,
    ThresholdValue,
    YamlKeyPath,
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
    application_payload_bytes_per_epoch,
    auprc,
    auroc,
    campaign_detection_rate,
    common_mode_suppression,
    decisive_order,
    earliest_local_stop,
    false_campaigns_per_ten_thousand_benign_epochs,
    finite_horizon_pfa_point_estimate,
    mean_log_evidence_growth,
    order_evidence_share,
    outside_conditioning_power_loss,
    paired_detection_indicator_difference,
    paired_stopping_time_difference,
    pfa_difference,
    registry_coalition_count,
    seed_level_odi_rate,
    throughput,
)
from fedcampaign_emhi.evaluation.records import (
    OperationalCalibration,
    SequentialTrajectory,
    odi_evaluation_record,
)
from fedcampaign_emhi.evaluation.scalability import (
    ScalabilityMeasurement,
    expected_scalability_coalitions,
    summarize_scalability,
)
from fedcampaign_emhi.evaluation.sequential import (
    TrajectoryCache,
    calibrate_client_local_operating_point,
    calibrate_global_operating_point,
    calibrate_operating_points,
    campaign_trajectory,
    global_stop_epoch,
    heldout_benign_false_stop_records,
    horizon_trajectory,
    local_stop_epochs,
    operational_lead,
    statistical_lead,
    trajectory_context_coverage,
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
    evaluate_fitted_pure_order_cell,
)
from fedcampaign_emhi.experiments.registry import (
    ExperimentContract,
    FullMethodSupportInputs,
    FullMethodSupportResult,
    assert_known_experiment,
    confirmatory_completeness_within_tolerance,
    evaluate_full_method_support,
    experiment_registry,
    matched_operating_point_requirement,
    median_of,
    median_operational_lead_criterion,
    paired_odi_advantage_criterion,
    strict_odi_rate_criterion,
)
from fedcampaign_emhi.experiments.robustness import (
    EpochEventVolume,
    detection_rate_loss_within_maximum,
    enumerate_benign_common_mode_plan,
    false_campaign_suppression_meets_minimum,
    federation_wide_epoch_event_counts,
    paired_false_campaign_difference,
    rolling_benign_horizons,
    select_high_volume_windows,
    stress_epoch_feature_values,
    window_event_counts,
)
from fedcampaign_emhi.experiments.synthetic import (
    EstimatorFeasibilityObservation,
    PureOrderObservation,
    PureOrderSeedMetrics,
    SelfExplanationObservation,
    SyntheticCellOutcome,
    run_synthetic_cell,
    synthetic_role_seeds,
)
from fedcampaign_emhi.synthetic.generators import validate_synthetic_generators
from fedcampaign_emhi.synthetic.pure_order import enumerate_pure_order_grid
from fedcampaign_emhi.synthetic.self_explanation import (
    analytic_direct_derivative,
    primary_directional_test_passes,
)


def campaign_dataset(
    loaded: LoadedScientificConfiguration, experiment_name: ExperimentName
) -> DatasetName:
    if experiment_name is ExperimentName.SECONDARY_CONTROLLED_TRACE_GENERALIZATION:
        return loaded.values.datasets.secondary.name
    return loaded.values.datasets.primary.name


def _run_resume_sequence() -> tuple[ComponentName, ...]:
    return (
        "validate required existing artifacts",
        "reuse compatible ancestors",
        "identify incompatible or incomplete artifacts",
        "invalidate only their descendants",
        "reconstruct the minimum required subgraph",
        "atomically publish completed outputs",
    )


@dataclass(frozen=True)
class ExperimentExecutionResult:
    experiment_name: ExperimentName
    state: ExperimentState
    run_record_path: Path
    completed_cell_count: RecordCount
    detail: ComponentName


@dataclass(frozen=True)
class MethodSeedOdi:
    seed: SeedValue
    method_value: MetricValue
    source_evaluation_id: ArtifactIdentity


@dataclass(frozen=True)
class _EmhiMethodSpecification:
    method_name: MethodName
    context_method: ContextMethodName
    maximum_order: CoalitionOrder
    purification_enabled: Boolean


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
        resume_sequence=_run_resume_sequence(),
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
    fingerprint = material_fingerprint(synthetic_invariant_boundary_digest(loaded.values), ())
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


def with_technical_retry[TechnicalRetryResult](
    loaded: LoadedScientificConfiguration,
    operation: Callable[[], TechnicalRetryResult],
) -> TechnicalRetryResult:
    retries = loaded.values.runtime.automatic_technical_retries_after_initial_failure
    last_error: OSError | MemoryError | None = None
    for _attempt in range(retries + 1):
        try:
            return operation()
        except (OSError, MemoryError) as error:
            last_error = error
    if last_error is None:
        raise RuntimeError("technical retry loop exited without an attempt")
    raise last_error


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
    composition_observations: list[CompositionCandidateObservation] = []
    for role in contract.execution_roles:
        methods: tuple[MethodName | None, ...] = contract.methods or (None,)
        for seed in synthetic_role_seeds(loaded, role):
            for method_name in methods:
                started = perf_counter()
                finite_horizon_metrics: FiniteHorizonSeedMetrics | None = None
                composition_metrics: CompositionCandidateSeedMetrics | None = None
                technical_failure = False
                try:
                    outcome = run_synthetic_cell_with_technical_retry(
                        loaded, experiment_name, seed, method_name, role
                    )
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
                            "operating_point_available": composition_metrics.calibrated_threshold
                            is not None,
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
                method_slug = (
                    "coordinate-validation"
                    if method_name is None
                    else method_artifact_stem(method_name)
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
                if (
                    state is ExperimentState.COMPLETED
                    and composition_metrics is not None
                    and method_name is not None
                ):
                    evidence = cast(Mapping[str, YamlNode], outcome.evidence)
                    composition_observations.append(
                        CompositionCandidateObservation(
                            method_name=method_name,
                            seed=seed,
                            standardized_target_order_error=cast(
                                StandardizedError, evidence["standardized_target_order_error"]
                            ),
                            metric=composition_metrics,
                            diagnostic_path=diagnostic_path,
                        )
                    )
                fingerprint = material_fingerprint(
                    synthetic_cell_boundary_digest(loaded.values),
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
    if experiment_name is ExperimentName.STRONG_COMPARATOR_COMPOSITION_CHALLENGE:
        materialize_strong_comparator_composition_selection(
            loaded,
            repository,
            tuple(composition_observations),
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
        "metric_name": "primary_attenuation_contrast",
        "method_name": "Exact Complement Exclusion",
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
        decision=(
            SupportState.SUPPORTED
            if primary_directional_test_passes(
                raw_p_value, loaded.values.statistics.nominal_significance_alpha
            )
            else SupportState.NULL_RESULT
        ),
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values), source_digests
        ),
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
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values), source_digests
        ),
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
    staging = layout.roots.outputs_root / "cache" / "staging"
    path = (
        layout.experiment_outputs_root(ExperimentName.STRONG_COMPARATOR_COMPOSITION_CHALLENGE)
        / "artifacts"
        / "derived"
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
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values), source_digests
        ),
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
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values), source_digests
        ),
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
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values), source_digests
        ),
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
    return _preprocessing_paths(loaded, repository, campaign_dataset(loaded, experiment_name))


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
    destination = detector_score_artifact_path(loaded, repository, dataset_name, root_seed)
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
    destination = marginal_rank_artifact_path(loaded, repository, dataset_name, root_seed)
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


def _campaign_rows(
    loaded: LoadedScientificConfiguration,
    scores: DetectorScoreArtifactRecord,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    campaigns: CampaignRegistryRecord,
    calibration: OperationalCalibration,
) -> tuple[tuple[YamlNode, ...], tuple[OdiIndicator, ...]]:
    rows: list[YamlNode] = []
    odi_values: list[OdiIndicator] = []
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
        odi_values.append(indicator)
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
                tuple(log(max(item.global_evidence_factor, 1.0)) for item in trajectory.epochs)
            )
        )
        scored_coalitions = 0 if stop_row is None else stop_row.scored_coalition_count
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
                "paired_stopping_time_difference": (
                    None
                    if global_stop is None or earliest_local is None
                    else paired_stopping_time_difference(global_stop, earliest_local)
                ),
                "paired_detection_indicator_difference": paired_detection_indicator_difference(
                    bool(odi.global_detection_indicator), earliest_local is not None
                ),
                "decisive_order": None if decisive is None else int(decisive),
                "order_evidence_share": order_share,
                "mean_log_evidence_growth": log_growth,
                "context_coverage": coverage,
                "abstention_rate": 1.0 - coverage,
                "server_latency_seconds": elapsed,
                "end_to_end_latency_seconds": elapsed,
                "throughput": None if elapsed <= 0.0 else throughput(scored_coalitions, elapsed),
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
            "global_evidence_factor": (
                1.0 if not trajectory.epochs else trajectory.epochs[-1].global_evidence_factor
            ),
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
        f"{method_artifact_stem(method_name)}.seed-{seed}"
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
        _preprocessing_paths(loaded, repository, campaign_dataset(loaded, experiment_name))
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
    campaign_rows, odi_values = _campaign_rows(
        loaded,
        scores,
        ranks,
        fit,
        campaigns,
        calibration,
    )
    heldout_rows = _heldout_rows(loaded, ranks, fit, partitions, calibration, trajectory_cache)
    heldout_maps = tuple(_as_mapping(row) for row in heldout_rows)
    campaign_maps = tuple(_as_mapping(row) for row in campaign_rows)
    heldout_false_stops = sum(int(cast(Boolean, row["false_campaign"])) for row in heldout_maps)
    heldout_epochs = sum(len(horizon.epoch_indexes) for horizon in partitions.heldout_horizons)
    false_campaign_rate = (
        None
        if heldout_epochs <= 0
        else false_campaigns_per_ten_thousand_benign_epochs(heldout_false_stops, heldout_epochs)
    )
    positive_scores = tuple(
        cast(DetectorScore, row["mean_log_evidence_growth"])
        for row in campaign_maps
        if row["mean_log_evidence_growth"] is not None
    )
    negative_scores = tuple(
        log(max(cast(DetectorScore, row["global_evidence_factor"]), 1.0)) for row in heldout_maps
    )
    ranking_scores = (*positive_scores, *negative_scores)
    ranking_labels = (
        *(True for _score in positive_scores),
        *(False for _score in negative_scores),
    )
    ranking_auroc = None if not ranking_scores else auroc(ranking_scores, ranking_labels)
    ranking_auprc = None if not ranking_scores else auprc(ranking_scores, ranking_labels)
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    staging = layout.roots.outputs_root / "cache" / "staging"
    method_slug = method_artifact_stem(method_name)
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
        "seed_strict_odi_rate": None if not odi_values else seed_level_odi_rate(odi_values),
        "false_campaigns_per_ten_thousand_benign_epochs": false_campaign_rate,
        "campaign_versus_heldout_auroc": (
            None if ranking_auroc is None else ranking_auroc.metric_value
        ),
        "campaign_versus_heldout_auprc": (
            None if ranking_auprc is None else ranking_auprc.metric_value
        ),
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


def _comparator_epoch_scores(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    ranks: MarginalRankArtifactRecord,
    method_name: MethodName,
) -> tuple[tuple[EpochIndexValue, DetectorScore], ...]:
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
    scores: list[tuple[EpochIndexValue, DetectorScore]] = []
    cusum_state: tuple[CusumState, ...] = ()
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
    raw_scores: tuple[tuple[EpochIndexValue, DetectorScore], ...],
    nuisance_epochs: tuple[EpochIndexValue, ...],
) -> tuple[tuple[EpochIndexValue, DetectorScore], ...]:
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
    evidence_scores: tuple[tuple[EpochIndexValue, DetectorScore], ...],
    epochs: tuple[EpochIndexValue, ...],
    threshold: ThresholdValue | None,
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
    evidence_scores: tuple[tuple[EpochIndexValue, DetectorScore], ...],
    partitions: BenignPartitionRecord,
) -> tuple[
    ThresholdValue | None, tuple[RecordCount, ...], RecordCount, RecordCount, FalseAlarmRate | None
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


def materialize_seed_statistics(
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
    expected_confirmatory = loaded.values.randomness.real_confirmatory_roots
    method_groups = [
        (method_name, records)
        for method_name, records in method_groups
        if confirmatory_completeness_within_tolerance(
            loaded,
            expected_confirmatory,
            tuple(
                record.seed
                for record in records
                if record.execution_role is ExecutionRole.CONFIRMATORY
            ),
        )
    ]
    if not method_groups:
        return ()
    raw_p_values: list[FalseAlarmRate] = []
    estimates: list[MetricRate] = []
    intervals: list[tuple[MetricRate, MetricRate] | None] = []
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
        fingerprints.append(
            material_fingerprint(statistical_analysis_boundary_digest(loaded.values), hashes)
        )
        if len(values) < 2:
            raw_p_values.append(1.0)
            intervals.append(None)
            continue
        flipped = exact_sign_flip_means(values)
        raw_p_values.append(sign_flip_p_value(estimate, flipped, True))
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
            root
            / "statistics"
            / "seed-level"
            / f"{method_artifact_stem(method_name)}-strict-odi-rate.json"
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
    dataset_name = campaign_dataset(loaded, experiment_name)
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
                / method_artifact_stem(MethodName.FULL_FEDCAMPAIGN_EMHI)
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
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values), source_digests
        ),
        content_digest=payload_digest(payload),
    )
    path = root / "statistics" / "tests" / "primary-holm-not-tested.json"
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    return path


def _hypothesis_artifact_stem(identifier: ComponentName) -> RelativePath:
    return identifier.lower().replace(" ", "-")


def _as_mapping(payload: YamlNode) -> Mapping[YamlKeyPath, YamlNode]:
    if not isinstance(payload, Mapping):
        raise ValueError("evaluation payload must be a mapping")
    return payload


def _load_seed_summaries(
    root: Path,
) -> tuple[tuple[Path, SeedSummaryRecord], ...]:
    summary_root = root / "metrics" / "seed-summaries"
    paths = tuple(sorted(summary_root.glob("**/*.json")))
    return tuple((path, SeedSummaryRecord.model_validate_json(path.read_bytes())) for path in paths)


def _confirmatory_method_summaries(
    summaries: tuple[tuple[Path, SeedSummaryRecord], ...],
    method_name: MethodName,
) -> tuple[tuple[Path, SeedSummaryRecord], ...]:
    return tuple(
        (path, record)
        for path, record in summaries
        if record.execution_role is ExecutionRole.CONFIRMATORY
        and record.method_name is method_name
        and record.metric_name == "strict_odi_rate"
    )


def _method_seed_odi(
    record: SeedSummaryRecord, summary_identity: ArtifactIdentity
) -> MethodSeedOdi:
    source_identity = (
        record.source_evaluation_ids[0] if record.source_evaluation_ids else summary_identity
    )
    return MethodSeedOdi(
        seed=record.seed,
        method_value=record.method_value,
        source_evaluation_id=source_identity,
    )


def _pair_confirmatory_odi(
    full_summaries: tuple[tuple[Path, SeedSummaryRecord], ...],
    comparator_summaries: tuple[tuple[Path, SeedSummaryRecord], ...],
) -> tuple[
    tuple[Path, ...],
    tuple[SeedSummaryRecord, ...],
    tuple[SeedSummaryRecord, ...],
    tuple[MethodSeedOdi, ...],
    tuple[MethodSeedOdi, ...],
]:
    comparator_by_seed = tuple((record.seed, path, record) for path, record in comparator_summaries)
    paired_paths: list[Path] = []
    paired_full_records: list[SeedSummaryRecord] = []
    paired_comparator_records: list[SeedSummaryRecord] = []
    paired_full_odi: list[MethodSeedOdi] = []
    paired_comparator_odi: list[MethodSeedOdi] = []
    for path, record in full_summaries:
        match = next(
            (
                (comparator_path, comparator_record)
                for seed, comparator_path, comparator_record in comparator_by_seed
                if seed == record.seed
            ),
            None,
        )
        if match is None:
            continue
        comparator_path, comparator_record = match
        full_identity = path.as_posix()
        comparator_identity = comparator_path.as_posix()
        paired_paths.extend((path, comparator_path))
        paired_full_records.append(record)
        paired_comparator_records.append(comparator_record)
        paired_full_odi.append(_method_seed_odi(record, full_identity))
        paired_comparator_odi.append(_method_seed_odi(comparator_record, comparator_identity))
    return (
        tuple(paired_paths),
        tuple(paired_full_records),
        tuple(paired_comparator_records),
        tuple(paired_full_odi),
        tuple(paired_comparator_odi),
    )


def _materialize_paired_confirmatory_odi_contrast(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    hypothesis_identifier: ComponentName,
    comparator_method: MethodName,
    metric_name: ComponentName,
) -> StatisticalRecord | None:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    summaries = _load_seed_summaries(root)
    full_summaries = _confirmatory_method_summaries(summaries, MethodName.FULL_FEDCAMPAIGN_EMHI)
    comparator_summaries = _confirmatory_method_summaries(summaries, comparator_method)
    paired_paths, paired_full, paired_comparator, paired_full_odi, paired_comparator_odi = (
        _pair_confirmatory_odi(full_summaries, comparator_summaries)
    )
    paired_seeds = tuple(item.seed for item in paired_full_odi)
    expected = loaded.values.randomness.real_confirmatory_roots
    source_ids = tuple(path.relative_to(repository).as_posix() for path in paired_paths)
    source_digests = tuple(file_sha256(path) for path in paired_paths)
    complete = confirmatory_completeness_within_tolerance(loaded, expected, paired_seeds)
    if not complete:
        payload: YamlNode = {
            "experiment_name": experiment_name.value,
            "hypothesis_identifier": hypothesis_identifier,
            "metric_name": metric_name,
            "method_name": MethodName.FULL_FEDCAMPAIGN_EMHI.value,
            "independent_unit_count": len(paired_seeds),
            "estimate": 0.0,
            "raw_p_value": None,
            "confidence_level": None,
            "confidence_lower": None,
            "confidence_upper": None,
            "hodges_lehmann_shift": None,
            "source_result_ids": list(source_ids),
        }
        record = StatisticalRecord(
            hypothesis_identifier=hypothesis_identifier,
            metric_name=metric_name,
            method_name=MethodName.FULL_FEDCAMPAIGN_EMHI.value,
            independent_unit_count=len(paired_seeds),
            estimate=0.0,
            raw_p_value=None,
            adjusted_p_value=None,
            confidence_level=None,
            confidence_lower=None,
            confidence_upper=None,
            hodges_lehmann_shift=None,
            decision=SupportState.NOT_TESTED,
            source_result_ids=source_ids,
            dependency_fingerprint=material_fingerprint(
                statistical_analysis_boundary_digest(loaded.values), source_digests
            ),
            content_digest=payload_digest(payload),
        )
        path = (
            root
            / "statistics"
            / "tests"
            / f"{_hypothesis_artifact_stem(hypothesis_identifier)}.json"
        )
        write_atomic_json(
            path,
            cast(YamlNode, record.model_dump(mode="json")),
            layout.roots.outputs_root / "cache" / "staging",
        )
        return record
    paired_with_difference = tuple(
        replace(
            full,
            reference_method_name=comparator.method_name,
            reference_value=comparator.method_value,
            paired_difference=full.method_value - comparator.method_value,
        )
        for full, comparator in zip(paired_full, paired_comparator, strict=True)
    )
    differences = paired_seed_differences(paired_with_difference)
    if len(differences) != len(paired_full_odi) or len(differences) != len(paired_comparator_odi):
        raise ValueError("paired ODI differences must preserve confirmatory seed pairing")
    estimate = sum(differences) / len(differences)
    shift = hodges_lehmann_shift(differences)
    raw_p_value = sign_flip_p_value(estimate, exact_sign_flip_means(differences), True)
    interval = paired_mean_bca_interval(
        differences,
        loaded.values.statistics.confidence_level,
        loaded.values.statistics.bootstrap_replicates,
        loaded.values.randomness.statistical_analysis_base_seed,
    )
    payload = {
        "experiment_name": experiment_name.value,
        "hypothesis_identifier": hypothesis_identifier,
        "metric_name": metric_name,
        "method_name": MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        "independent_unit_count": len(differences),
        "estimate": estimate,
        "raw_p_value": raw_p_value,
        "confidence_level": loaded.values.statistics.confidence_level,
        "confidence_lower": interval[0],
        "confidence_upper": interval[1],
        "hodges_lehmann_shift": shift,
        "source_result_ids": list(source_ids),
    }
    record = StatisticalRecord(
        hypothesis_identifier=hypothesis_identifier,
        metric_name=metric_name,
        method_name=MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        independent_unit_count=len(differences),
        estimate=estimate,
        raw_p_value=raw_p_value,
        adjusted_p_value=None,
        confidence_level=loaded.values.statistics.confidence_level,
        confidence_lower=interval[0],
        confidence_upper=interval[1],
        hodges_lehmann_shift=shift,
        decision=(
            SupportState.SUPPORTED
            if raw_p_value < loaded.values.statistics.nominal_significance_alpha
            else SupportState.NULL_RESULT
        ),
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values), source_digests
        ),
        content_digest=payload_digest(payload),
    )
    path = (
        root / "statistics" / "tests" / f"{_hypothesis_artifact_stem(hypothesis_identifier)}.json"
    )
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    return record


def _confirmatory_raw_evaluation_paths(root: Path, method_name: MethodName) -> tuple[Path, ...]:
    return tuple(
        sorted(
            (
                root
                / "evaluations"
                / "raw"
                / ExecutionRole.CONFIRMATORY.value
                / method_artifact_stem(method_name)
            ).glob("*.json")
        )
    )


def _evaluation_heldout_upper_pfa(payload: Mapping[YamlKeyPath, YamlNode]) -> Probability | None:
    calibration = _as_mapping(payload["calibration"])
    global_point = _as_mapping(calibration["global"])
    heldout = global_point["heldout_upper_pfa"]
    if heldout is None:
        return None
    return cast(Probability, heldout)


def _evaluation_operating_point_available(payload: Mapping[YamlKeyPath, YamlNode]) -> Boolean:
    calibration = _as_mapping(payload["calibration"])
    global_point = _as_mapping(calibration["global"])
    return global_point["threshold"] is not None


def _evaluation_success_leads(
    payload: Mapping[YamlKeyPath, YamlNode],
) -> tuple[OperationalLeadEpochs, ...]:
    campaigns = payload["campaigns"]
    if not isinstance(campaigns, Sequence):
        return ()
    leads: list[OperationalLeadEpochs] = []
    for row in campaigns:
        if not isinstance(row, Mapping):
            continue
        if row["strict_odi"] != 1:
            continue
        lead = row["operational_lead_epochs"]
        if lead is None:
            continue
        leads.append(cast(OperationalLeadEpochs, lead))
    return tuple(leads)


def _materialize_full_method_support(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    contrast: StatisticalRecord | None,
) -> Path | None:
    if contrast is None or contrast.raw_p_value is None:
        return None
    dataset_name = campaign_dataset(loaded, ExperimentName.PRIMARY_STRICT_ODI_EVALUATION)
    prepared_path = _preprocessing_paths(loaded, repository, dataset_name)[1]
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    if not prepared.selected_client_ids:
        return None
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(ExperimentName.PRIMARY_STRICT_ODI_EVALUATION)
    full_paths = _confirmatory_raw_evaluation_paths(root, MethodName.FULL_FEDCAMPAIGN_EMHI)
    comparator_paths = _confirmatory_raw_evaluation_paths(
        root, MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI
    )
    expected = loaded.values.randomness.real_confirmatory_roots
    full_payloads = tuple(
        _as_mapping(cast(YamlNode, json.loads(path.read_text(encoding="utf-8"))))
        for path in full_paths
    )
    comparator_payloads = tuple(
        _as_mapping(cast(YamlNode, json.loads(path.read_text(encoding="utf-8"))))
        for path in comparator_paths
    )
    full_seeds = tuple(cast(SeedValue, payload["seed"]) for payload in full_payloads)
    comparator_seeds = tuple(cast(SeedValue, payload["seed"]) for payload in comparator_payloads)
    if not confirmatory_completeness_within_tolerance(
        loaded, expected, full_seeds
    ) or not confirmatory_completeness_within_tolerance(loaded, expected, comparator_seeds):
        return None
    upper_bounds = tuple(_evaluation_heldout_upper_pfa(payload) for payload in full_payloads)
    if any(bound is None for bound in upper_bounds):
        return None
    heldout_upper = max(cast(tuple[Probability, ...], upper_bounds))
    summaries = _confirmatory_method_summaries(
        _load_seed_summaries(root), MethodName.FULL_FEDCAMPAIGN_EMHI
    )
    if not summaries:
        return None
    mean_strict_odi_rate = sum(record.method_value for _path, record in summaries) / len(summaries)
    success_leads = tuple(
        lead for payload in full_payloads for lead in _evaluation_success_leads(payload)
    )
    materiality = loaded.values.materiality.primary_real
    target_pfa = loaded.values.evidence.calibrated_finite_horizon.target_pfa
    nominal_alpha = loaded.values.statistics.nominal_significance_alpha
    full_available = all(
        _evaluation_operating_point_available(payload) for payload in full_payloads
    )
    comparator_available = all(
        _evaluation_operating_point_available(payload) for payload in comparator_payloads
    )
    paired_advantage = contrast.estimate
    pfa_ok = heldout_upper <= target_pfa
    odi_ok = strict_odi_rate_criterion(mean_strict_odi_rate, materiality.minimum_strict_odi_rate)
    advantage_ok = paired_odi_advantage_criterion(
        paired_advantage, materiality.minimum_odi_rate_advantage_over_order_at_most_two
    )
    matched_ok = matched_operating_point_requirement(full_available, comparator_available)
    directional_ok = contrast.raw_p_value < nominal_alpha
    if success_leads:
        median_lead = median_of(success_leads)
        lead_ok = median_operational_lead_criterion(
            median_lead, materiality.minimum_median_operational_lead_epochs
        )
        result = evaluate_full_method_support(
            FullMethodSupportInputs(
                heldout_pfa_upper_bound=heldout_upper,
                target_pfa=target_pfa,
                mean_strict_odi_rate=mean_strict_odi_rate,
                minimum_strict_odi_rate=materiality.minimum_strict_odi_rate,
                paired_odi_advantage=paired_advantage,
                minimum_odi_advantage=materiality.minimum_odi_rate_advantage_over_order_at_most_two,
                median_lead_among_successes=median_lead,
                minimum_median_lead=materiality.minimum_median_operational_lead_epochs,
                directional_adjusted_p_value=contrast.raw_p_value,
                nominal_alpha=nominal_alpha,
                full_operating_point_available=full_available,
                comparator_operating_point_available=comparator_available,
            )
        )
        if result.lead_criterion_satisfied is not lead_ok:
            raise ValueError("full-method lead criterion is inconsistent")
        if result.pfa_criterion_satisfied is not pfa_ok:
            raise ValueError("full-method PFA criterion is inconsistent")
        if result.odi_rate_criterion_satisfied is not odi_ok:
            raise ValueError("full-method ODI-rate criterion is inconsistent")
        if result.advantage_criterion_satisfied is not advantage_ok:
            raise ValueError("full-method advantage criterion is inconsistent")
        if result.matched_operating_point_criterion_satisfied is not matched_ok:
            raise ValueError("full-method operating-point criterion is inconsistent")
        if result.directional_criterion_satisfied is not directional_ok:
            raise ValueError("full-method directional criterion is inconsistent")
    else:
        result = FullMethodSupportResult(
            pfa_criterion_satisfied=pfa_ok,
            odi_rate_criterion_satisfied=odi_ok,
            advantage_criterion_satisfied=advantage_ok,
            lead_criterion_satisfied=False,
            directional_criterion_satisfied=directional_ok,
            matched_operating_point_criterion_satisfied=matched_ok,
        )
    source_paths = (*full_paths, *comparator_paths)
    source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
    source_digests = tuple(file_sha256(path) for path in source_paths)
    all_criteria_pass = (
        result.pfa_criterion_satisfied
        and result.odi_rate_criterion_satisfied
        and result.advantage_criterion_satisfied
        and result.lead_criterion_satisfied
        and result.directional_criterion_satisfied
        and result.matched_operating_point_criterion_satisfied
    )
    median_lead_value = None if not success_leads else median_of(success_leads)
    payload: YamlNode = {
        "experiment_name": ExperimentName.PRIMARY_STRICT_ODI_EVALUATION.value,
        "heldout_pfa_upper_bound": heldout_upper,
        "mean_strict_odi_rate": mean_strict_odi_rate,
        "paired_odi_advantage": paired_advantage,
        "median_lead_among_successes": median_lead_value,
        "directional_adjusted_p_value": contrast.raw_p_value,
        "pfa_criterion_satisfied": result.pfa_criterion_satisfied,
        "odi_rate_criterion_satisfied": result.odi_rate_criterion_satisfied,
        "advantage_criterion_satisfied": result.advantage_criterion_satisfied,
        "lead_criterion_satisfied": result.lead_criterion_satisfied,
        "directional_criterion_satisfied": result.directional_criterion_satisfied,
        "matched_operating_point_criterion_satisfied": result.matched_operating_point_criterion_satisfied,
        "all_criteria_pass": all_criteria_pass,
        "source_result_ids": list(source_ids),
    }
    record = FullMethodSupportRecord(
        experiment_name=ExperimentName.PRIMARY_STRICT_ODI_EVALUATION,
        heldout_pfa_upper_bound=heldout_upper,
        mean_strict_odi_rate=mean_strict_odi_rate,
        paired_odi_advantage=paired_advantage,
        median_lead_among_successes=median_lead_value,
        directional_adjusted_p_value=contrast.raw_p_value,
        pfa_criterion_satisfied=result.pfa_criterion_satisfied,
        odi_rate_criterion_satisfied=result.odi_rate_criterion_satisfied,
        advantage_criterion_satisfied=result.advantage_criterion_satisfied,
        lead_criterion_satisfied=result.lead_criterion_satisfied,
        directional_criterion_satisfied=result.directional_criterion_satisfied,
        matched_operating_point_criterion_satisfied=result.matched_operating_point_criterion_satisfied,
        all_criteria_pass=all_criteria_pass,
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values), source_digests
        ),
        content_digest=payload_digest(payload),
    )
    path = root / "statistics" / "tests" / "full-method-support.json"
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    return path


def _materialize_confirmatory_odi_inferences(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    primary_not_tested: Boolean,
) -> None:
    if experiment_name is ExperimentName.PRIMARY_STRICT_ODI_EVALUATION and not primary_not_tested:
        contrast = _materialize_paired_confirmatory_odi_contrast(
            loaded,
            repository,
            experiment_name,
            PrimaryHolmHypothesis.PRIMARY_ODI_ADVANTAGE_OVER_ORDER_AT_MOST_TWO_EMHI.value,
            MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI,
            "paired_strict_odi_rate_advantage",
        )
        _materialize_full_method_support(loaded, repository, contrast)
        return
    if experiment_name not in {
        ExperimentName.EXCLUSION_MECHANISM_ABLATION,
        ExperimentName.PURIFICATION_AND_ORDER_ABLATION,
    }:
        return
    for family_experiment, hypothesis, comparator_method in SECONDARY_HOLM_STATISTICS:
        if family_experiment is not experiment_name:
            continue
        _materialize_paired_confirmatory_odi_contrast(
            loaded,
            repository,
            experiment_name,
            hypothesis.value,
            comparator_method,
            "paired_strict_odi_rate_advantage",
        )


def _stress_window_false_declaration_rate(
    config: ScientificConfig,
    ranks: MarginalRankArtifactRecord,
    fit: EMHIFitArtifactRecord,
    threshold: ThresholdValue | None,
    stress_windows: tuple[BenignHorizon, ...],
    trajectory_cache: TrajectoryCache,
) -> MetricRate | None:
    if threshold is None or not stress_windows:
        return None
    stops = tuple(
        global_stop_epoch(
            horizon_trajectory(
                config,
                ranks,
                fit,
                BenignHorizonRecord(
                    start_epoch=window.start_epoch, epoch_indexes=window.epoch_indexes
                ),
                None,
                trajectory_cache,
            ),
            threshold,
        )
        is not None
        for window in stress_windows
    )
    return sum(stops) / len(stops)


def _comparator_stress_window_false_declaration_rate(
    evidence_scores: tuple[tuple[EpochIndexValue, DetectorScore], ...],
    threshold: ThresholdValue | None,
    stress_windows: tuple[BenignHorizon, ...],
) -> MetricRate | None:
    if threshold is None or not stress_windows:
        return None
    stops = tuple(
        _comparator_stop(evidence_scores, window.epoch_indexes, threshold) is not None
        for window in stress_windows
    )
    return sum(stops) / len(stops)


def _benign_common_mode_seed_fcr(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    seed: SeedValue,
    stress_windows: tuple[BenignHorizon, ...],
) -> tuple[MetricRate, MetricRate, tuple[Path, ...]] | None:
    _inventory_path, _prepared_path, split_path, partitions_path, _campaigns_path = (
        _preprocessing_paths(loaded, repository, dataset_name)
    )
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    partitions = BenignPartitionRecord.model_validate_json(partitions_path.read_bytes())
    score_path = with_technical_retry(
        loaded,
        partial(_materialize_detector_scores, loaded, repository, dataset_name, seed),
    )
    rank_path = with_technical_retry(
        loaded,
        partial(_materialize_marginal_ranks, loaded, repository, dataset_name, seed, score_path),
    )
    ranks = MarginalRankArtifactRecord.model_validate_json(rank_path.read_bytes())
    fit_path = with_technical_retry(
        loaded,
        partial(
            _materialize_emhi_fit,
            loaded,
            repository,
            dataset_name,
            seed,
            MethodName.FULL_FEDCAMPAIGN_EMHI,
            score_path,
            rank_path,
        ),
    )
    fit = EMHIFitArtifactRecord.model_validate_json(fit_path.read_bytes())
    emhi_calibration = calibrate_global_operating_point(loaded.values, ranks, fit, partitions)
    trajectory_cache = TrajectoryCache()
    emhi_fcr = _stress_window_false_declaration_rate(
        loaded.values,
        ranks,
        fit,
        emhi_calibration.threshold,
        stress_windows,
        trajectory_cache,
    )
    raw_scores = _comparator_epoch_scores(
        loaded, repository, ranks, MethodName.RAW_MEAN_RANK_FUSION
    )
    comparator_scores = _comparator_evidence_scores(loaded, raw_scores, split.nuisance_fit_epochs)
    comparator_threshold, *_rest = _calibrate_comparator_operating_point(
        loaded, comparator_scores, partitions
    )
    raw_mean_fcr = _comparator_stress_window_false_declaration_rate(
        comparator_scores, comparator_threshold, stress_windows
    )
    if emhi_fcr is None or raw_mean_fcr is None:
        return None
    return emhi_fcr, raw_mean_fcr, (score_path, rank_path, fit_path)


def _benign_common_mode_seed_difference(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    seed: SeedValue,
    stress_windows: tuple[BenignHorizon, ...],
) -> tuple[MetricRate, tuple[Path, ...]] | None:
    outcome = _benign_common_mode_seed_fcr(loaded, repository, dataset_name, seed, stress_windows)
    if outcome is None:
        return None
    emhi_fcr, raw_mean_fcr, paths = outcome
    reduction = paired_false_campaign_difference(raw_mean_fcr, emhi_fcr)
    if reduction != pfa_difference(raw_mean_fcr, emhi_fcr):
        raise ValueError("false-campaign reduction must match the PFA difference")
    return reduction, paths


def materialize_benign_common_mode_statistic(
    loaded: LoadedScientificConfiguration,
    repository: Path,
) -> Path | None:
    experiment_name = ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS
    plan = enumerate_benign_common_mode_plan(loaded.values)
    required_methods = {
        MethodName.FULL_FEDCAMPAIGN_EMHI,
        MethodName.RAW_MEAN_RANK_FUSION,
    }
    if not required_methods.issubset(plan.methods):
        return None
    _inventory_path, prepared_path, split_path, _partitions_path, _campaigns_path = (
        _preprocessing_paths(loaded, repository, plan.dataset_name)
    )
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    if not prepared.selected_client_ids:
        return None
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    horizon_length = loaded.values.campaign.evaluation_horizon_epochs
    all_windows = rolling_benign_horizons(
        split.heldout_benign_epochs,
        horizon_length,
        plan.stress_stride_epochs,
    )
    if not all_windows:
        return None
    epoch_volumes = tuple(
        EpochEventVolume(
            client_id=epoch.client_id,
            epoch_index=epoch.epoch_index,
            raw_event_count=epoch.raw_event_count,
        )
        for epoch in prepared.epochs
    )
    epoch_totals = federation_wide_epoch_event_counts(epoch_volumes, prepared.selected_client_ids)
    counts = window_event_counts(all_windows, epoch_totals)
    stress_windows = select_high_volume_windows(all_windows, counts, plan.top_event_count_fraction)
    expected_confirmatory = loaded.values.randomness.real_confirmatory_roots
    differences: list[MetricRate] = []
    source_paths: list[Path] = []
    covered_seeds: list[SeedValue] = []
    for seed in expected_confirmatory:
        outcome = _benign_common_mode_seed_difference(
            loaded, repository, plan.dataset_name, seed, stress_windows
        )
        if outcome is None:
            continue
        difference, seed_paths = outcome
        differences.append(difference)
        source_paths.extend(seed_paths)
        covered_seeds.append(seed)
    if not confirmatory_completeness_within_tolerance(
        loaded, expected_confirmatory, tuple(covered_seeds)
    ):
        return None
    estimate = sum(differences) / len(differences)
    shift = hodges_lehmann_shift(tuple(differences))
    flipped = exact_sign_flip_means(tuple(differences))
    raw_p_value = sign_flip_p_value(estimate, flipped, True)
    interval = paired_mean_bca_interval(
        tuple(differences),
        loaded.values.statistics.confidence_level,
        loaded.values.statistics.bootstrap_replicates,
        loaded.values.randomness.statistical_analysis_base_seed,
    )
    source_digests = tuple(file_sha256(path) for path in source_paths)
    source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
    payload: YamlNode = {
        "experiment_name": experiment_name.value,
        "hypothesis_identifier": PrimaryHolmHypothesis.COMMON_MODE_FALSE_CAMPAIGN_REDUCTION.value,
        "metric_name": "false_campaign_reduction",
        "method_name": MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        "independent_unit_count": len(differences),
        "estimate": estimate,
        "raw_p_value": raw_p_value,
        "confidence_level": loaded.values.statistics.confidence_level,
        "confidence_lower": interval[0],
        "confidence_upper": interval[1],
        "hodges_lehmann_shift": shift,
        "source_result_ids": list(source_ids),
    }
    record = StatisticalRecord(
        hypothesis_identifier=PrimaryHolmHypothesis.COMMON_MODE_FALSE_CAMPAIGN_REDUCTION.value,
        metric_name="false_campaign_reduction",
        method_name=MethodName.FULL_FEDCAMPAIGN_EMHI.value,
        independent_unit_count=len(differences),
        estimate=estimate,
        raw_p_value=raw_p_value,
        adjusted_p_value=None,
        confidence_level=loaded.values.statistics.confidence_level,
        confidence_lower=interval[0],
        confidence_upper=interval[1],
        hodges_lehmann_shift=shift,
        decision=(
            SupportState.SUPPORTED
            if raw_p_value < loaded.values.statistics.nominal_significance_alpha
            else SupportState.NULL_RESULT
        ),
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values), source_digests
        ),
        content_digest=payload_digest(payload),
    )
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    path = root / "statistics" / "tests" / "common-mode-false-campaign-reduction.json"
    write_atomic_json(
        path,
        cast(YamlNode, record.model_dump(mode="json")),
        layout.roots.outputs_root / "cache" / "staging",
    )
    return path


def _apply_client_scaler(
    scaler: ClientFeatureScalerRecord, values: tuple[FeatureValue, ...]
) -> tuple[FeatureValue, ...]:
    return tuple(
        apply_robust_scaler(
            RobustScaler(median=median, iqr=iqr, iqr_floor=scaler.iqr_floor), (value,)
        )[0]
        for median, iqr, value in zip(scaler.medians, scaler.iqrs, values, strict=True)
    )


def _stressed_detector_scores(
    loaded: LoadedScientificConfiguration,
    prepared: PreparedDatasetRecord,
    split: DatasetSplitRecord,
    scores: DetectorScoreArtifactRecord,
    dataset_name: DatasetName,
    root_seed: SeedValue,
    stress_epoch_indexes: tuple[EpochIndexValue, ...],
    factor: RobustnessCountMultiplier,
) -> DetectorScoreArtifactRecord:
    assignments = assign_detector_families(split.selected_client_ids)
    stress_epoch_set = set(stress_epoch_indexes)
    nuisance_epoch_set = set(split.nuisance_fit_epochs)
    scalers_by_client = {scaler.client_id: scaler for scaler in prepared.client_scalers}
    streams: list[ClientDetectorScoreStream] = []
    for assignment in assignments:
        client_rows = tuple(row for row in prepared.epochs if row.client_id == assignment.client_id)
        fit_rows = tuple(
            row.feature_values
            for row in client_rows
            if row.epoch_index in split.detector_fit_epochs
        )
        scaler = scalers_by_client[assignment.client_id]
        stress_rows = tuple(
            _apply_client_scaler(
                scaler, stress_epoch_feature_values(row.unscaled_feature_values, factor)
            )
            for row in client_rows
            if row.epoch_index in stress_epoch_set
        )
        seed = detector_seed(root_seed, dataset_name, assignment.client_id)
        stress_scores = score_client(
            loaded.values, assignment.family, fit_rows, stress_rows, seed, assignment.client_id
        )
        stress_epochs = tuple(
            row.epoch_index for row in client_rows if row.epoch_index in stress_epoch_set
        )
        original_stream = next(
            stream for stream in scores.client_streams if stream.client_id == assignment.client_id
        )
        nuisance_pairs = tuple(
            (epoch, score)
            for epoch, score in zip(
                original_stream.epoch_indexes, original_stream.scores, strict=True
            )
            if epoch in nuisance_epoch_set
        )
        stress_pairs = tuple(zip(stress_epochs, stress_scores, strict=True))
        combined = tuple(sorted((*nuisance_pairs, *stress_pairs)))
        streams.append(
            ClientDetectorScoreStream(
                client_id=assignment.client_id,
                detector_family=assignment.family,
                detector_seed=seed,
                epoch_indexes=tuple(epoch for epoch, _score in combined),
                scores=tuple(score for _epoch, score in combined),
            )
        )
    return DetectorScoreArtifactRecord(
        dataset_name=dataset_name,
        root_seed=root_seed,
        selected_client_ids=split.selected_client_ids,
        client_streams=tuple(streams),
        dependency_fingerprint=scores.dependency_fingerprint,
    )


def _count_stress_false_declaration_rates(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    dataset_name: DatasetName,
    seed: SeedValue,
    factor: RobustnessCountMultiplier,
) -> tuple[MetricRate, MetricRate, tuple[Path, ...]] | None:
    _inventory_path, prepared_path, split_path, partitions_path, _campaigns_path = (
        _preprocessing_paths(loaded, repository, dataset_name)
    )
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    partitions = BenignPartitionRecord.model_validate_json(partitions_path.read_bytes())
    stress_windows = tuple(
        BenignHorizon(start_epoch=horizon.start_epoch, epoch_indexes=horizon.epoch_indexes)
        for horizon in partitions.heldout_horizons
    )
    if not stress_windows:
        return None
    stress_epoch_indexes = tuple(
        sorted({epoch for horizon in stress_windows for epoch in horizon.epoch_indexes})
    )
    score_path = with_technical_retry(
        loaded,
        partial(_materialize_detector_scores, loaded, repository, dataset_name, seed),
    )
    rank_path = with_technical_retry(
        loaded,
        partial(_materialize_marginal_ranks, loaded, repository, dataset_name, seed, score_path),
    )
    scores = DetectorScoreArtifactRecord.model_validate_json(score_path.read_bytes())
    stressed_scores = _stressed_detector_scores(
        loaded, prepared, split, scores, dataset_name, seed, stress_epoch_indexes, factor
    )
    stressed_ranks = build_marginal_rank_artifact(
        stressed_scores,
        split.nuisance_fit_epochs,
        loaded.values.context.rank_clip_epsilon,
        stressed_scores.dependency_fingerprint,
    )
    fit_path = with_technical_retry(
        loaded,
        partial(
            _materialize_emhi_fit,
            loaded,
            repository,
            dataset_name,
            seed,
            MethodName.FULL_FEDCAMPAIGN_EMHI,
            score_path,
            rank_path,
        ),
    )
    fit = EMHIFitArtifactRecord.model_validate_json(fit_path.read_bytes())
    emhi_calibration = calibrate_global_operating_point(
        loaded.values, stressed_ranks, fit, partitions
    )
    trajectory_cache = TrajectoryCache()
    emhi_fcr = _stress_window_false_declaration_rate(
        loaded.values,
        stressed_ranks,
        fit,
        emhi_calibration.threshold,
        stress_windows,
        trajectory_cache,
    )
    raw_scores = _comparator_epoch_scores(
        loaded, repository, stressed_ranks, MethodName.RAW_MEAN_RANK_FUSION
    )
    comparator_scores = _comparator_evidence_scores(loaded, raw_scores, split.nuisance_fit_epochs)
    comparator_threshold, *_rest = _calibrate_comparator_operating_point(
        loaded, comparator_scores, partitions
    )
    raw_mean_fcr = _comparator_stress_window_false_declaration_rate(
        comparator_scores, comparator_threshold, stress_windows
    )
    if emhi_fcr is None or raw_mean_fcr is None:
        return None
    return emhi_fcr, raw_mean_fcr, (score_path, rank_path, fit_path)


def materialize_benign_common_mode_count_stress_diagnostics(
    loaded: LoadedScientificConfiguration,
    repository: Path,
) -> tuple[Path, ...]:
    experiment_name = ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS
    plan = enumerate_benign_common_mode_plan(loaded.values)
    required_methods = {MethodName.FULL_FEDCAMPAIGN_EMHI, MethodName.RAW_MEAN_RANK_FUSION}
    if not required_methods.issubset(plan.methods):
        return ()
    _inventory_path, prepared_path, _split_path, _partitions_path, _campaigns_path = (
        _preprocessing_paths(loaded, repository, plan.dataset_name)
    )
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    if not prepared.selected_client_ids:
        return ()
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    staging = layout.roots.outputs_root / "cache" / "staging"
    paths: list[Path] = []
    for factor in loaded.values.robustness.benign_count_multiplication_factors:
        for seed in loaded.values.randomness.real_confirmatory_roots:
            outcome = _count_stress_false_declaration_rates(
                loaded, repository, plan.dataset_name, seed, factor
            )
            if outcome is None:
                continue
            emhi_fcr, raw_mean_fcr, source_paths = outcome
            source_digests = tuple(file_sha256(path) for path in source_paths)
            source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
            payload: YamlNode = {
                "seed": seed,
                "multiplication_factor": factor,
                "emhi_false_declaration_rate": emhi_fcr,
                "raw_mean_false_declaration_rate": raw_mean_fcr,
                "source_result_ids": list(source_ids),
            }
            record = CountStressDiagnosticRecord(
                seed=seed,
                multiplication_factor=factor,
                emhi_false_declaration_rate=emhi_fcr,
                raw_mean_false_declaration_rate=raw_mean_fcr,
                source_result_ids=source_ids,
                dependency_fingerprint=material_fingerprint(
                    statistical_analysis_boundary_digest(loaded.values), source_digests
                ),
                content_digest=payload_digest(payload),
            )
            path = root / "diagnostics" / "count-stress" / f"factor-{factor}" / f"seed-{seed}.json"
            write_atomic_json(path, cast(YamlNode, record.model_dump(mode="json")), staging)
            paths.append(path)
    return tuple(paths)


def _campaign_detection_rate_for_method(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    dataset_name: DatasetName,
    method_name: MethodName,
    seed: SeedValue,
) -> tuple[MetricRate, tuple[Path, ...]] | None:
    _inventory_path, _prepared_path, split_path, partitions_path, campaigns_path = (
        _preprocessing_paths(loaded, repository, dataset_name)
    )
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    partitions = BenignPartitionRecord.model_validate_json(partitions_path.read_bytes())
    campaigns = CampaignRegistryRecord.model_validate_json(campaigns_path.read_bytes())
    score_path = with_technical_retry(
        loaded,
        partial(_materialize_detector_scores, loaded, repository, dataset_name, seed),
    )
    rank_path = with_technical_retry(
        loaded,
        partial(_materialize_marginal_ranks, loaded, repository, dataset_name, seed, score_path),
    )
    fit_path = with_technical_retry(
        loaded,
        partial(
            _materialize_emhi_fit,
            loaded,
            repository,
            dataset_name,
            seed,
            method_name,
            score_path,
            rank_path,
        ),
    )
    scores = DetectorScoreArtifactRecord.model_validate_json(score_path.read_bytes())
    ranks = MarginalRankArtifactRecord.model_validate_json(rank_path.read_bytes())
    fit = EMHIFitArtifactRecord.model_validate_json(fit_path.read_bytes())
    target_local_pfa = _local_pfa_target(loaded, experiment_name)
    calibration = calibrate_operating_points(
        loaded.values,
        scores,
        ranks,
        fit,
        split.nuisance_fit_epochs,
        partitions,
        target_local_pfa,
    )
    rows, _odi_values = _campaign_rows(loaded, scores, ranks, fit, campaigns, calibration)
    typed_rows = tuple(cast(Mapping[str, YamlNode], row) for row in rows)
    if not typed_rows:
        return None
    detection_rate = campaign_detection_rate(
        tuple(cast(EpochIndexValue | None, row["global_stop_epoch"]) for row in typed_rows),
        loaded.values.campaign.evaluation_horizon_epochs,
    )
    return detection_rate, (score_path, rank_path, fit_path)


def materialize_benign_common_mode_positive_power_measurement(
    loaded: LoadedScientificConfiguration,
    repository: Path,
) -> Path | None:
    experiment_name = ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS
    plan = enumerate_benign_common_mode_plan(loaded.values)
    required_methods = {
        MethodName.FULL_FEDCAMPAIGN_EMHI,
        MethodName.RAW_MEAN_RANK_FUSION,
        MethodName.NO_OUTSIDE_CONTEXT_FULL_HIERARCHY,
    }
    if not required_methods.issubset(plan.methods):
        return None
    _inventory_path, prepared_path, split_path, _partitions_path, _campaigns_path = (
        _preprocessing_paths(loaded, repository, plan.dataset_name)
    )
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    if not prepared.selected_client_ids:
        return None
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    horizon_length = loaded.values.campaign.evaluation_horizon_epochs
    all_windows = rolling_benign_horizons(
        split.heldout_benign_epochs, horizon_length, plan.stress_stride_epochs
    )
    if not all_windows:
        return None
    epoch_volumes = tuple(
        EpochEventVolume(
            client_id=epoch.client_id,
            epoch_index=epoch.epoch_index,
            raw_event_count=epoch.raw_event_count,
        )
        for epoch in prepared.epochs
    )
    epoch_totals = federation_wide_epoch_event_counts(epoch_volumes, prepared.selected_client_ids)
    counts = window_event_counts(all_windows, epoch_totals)
    stress_windows = select_high_volume_windows(all_windows, counts, plan.top_event_count_fraction)
    materiality = loaded.values.materiality.benign_common_mode
    floor = loaded.values.numerics.metric_denominator_floor
    power_losses: list[MetricRate] = []
    suppressions: list[MetricRate] = []
    source_paths: list[Path] = []
    covered_seeds: list[SeedValue] = []
    for seed in loaded.values.randomness.real_confirmatory_roots:
        emhi_dr_outcome = _campaign_detection_rate_for_method(
            loaded,
            repository,
            experiment_name,
            plan.dataset_name,
            MethodName.FULL_FEDCAMPAIGN_EMHI,
            seed,
        )
        no_outside_dr_outcome = _campaign_detection_rate_for_method(
            loaded,
            repository,
            experiment_name,
            plan.dataset_name,
            MethodName.NO_OUTSIDE_CONTEXT_FULL_HIERARCHY,
            seed,
        )
        fcr_outcome = _benign_common_mode_seed_fcr(
            loaded, repository, plan.dataset_name, seed, stress_windows
        )
        if emhi_dr_outcome is None or no_outside_dr_outcome is None or fcr_outcome is None:
            continue
        emhi_dr, emhi_dr_paths = emhi_dr_outcome
        no_outside_dr, no_outside_dr_paths = no_outside_dr_outcome
        emhi_fcr, raw_mean_fcr, fcr_paths = fcr_outcome
        power_losses.append(outside_conditioning_power_loss(no_outside_dr, emhi_dr))
        suppressions.append(common_mode_suppression(emhi_fcr, raw_mean_fcr, floor))
        source_paths.extend((*emhi_dr_paths, *no_outside_dr_paths, *fcr_paths))
        covered_seeds.append(seed)
    if not confirmatory_completeness_within_tolerance(
        loaded, loaded.values.randomness.real_confirmatory_roots, tuple(covered_seeds)
    ):
        return None
    mean_power_loss = sum(power_losses) / len(power_losses)
    mean_suppression = sum(suppressions) / len(suppressions)
    source_digests = tuple(file_sha256(path) for path in source_paths)
    source_ids = tuple(path.relative_to(repository).as_posix() for path in source_paths)
    payload: YamlNode = {
        "independent_unit_count": len(covered_seeds),
        "mean_detection_rate_power_loss": mean_power_loss,
        "mean_common_mode_suppression": mean_suppression,
        "source_result_ids": list(source_ids),
    }
    record = BenignCommonModePositivePowerMeasurementRecord(
        independent_unit_count=len(covered_seeds),
        mean_detection_rate_power_loss=mean_power_loss,
        detection_rate_loss_within_maximum=detection_rate_loss_within_maximum(
            mean_power_loss, materiality.maximum_detection_rate_loss
        ),
        mean_common_mode_suppression=mean_suppression,
        false_campaign_suppression_meets_minimum=false_campaign_suppression_meets_minimum(
            mean_suppression, materiality.minimum_false_campaign_suppression
        ),
        source_result_ids=source_ids,
        dependency_fingerprint=material_fingerprint(
            statistical_analysis_boundary_digest(loaded.values), source_digests
        ),
        content_digest=payload_digest(payload),
    )
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    path = root / "diagnostics" / "positive-power" / "measurement.json"
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
    dataset_name = campaign_dataset(loaded, experiment_name)
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
    odi_values: list[OdiRateAdvantage] = []
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
    evaluation_id = _evaluation_artifact_id(experiment_name, execution_role, method_name, seed)
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
        / f"cell-{execution_role.value}-{method_artifact_stem(method_name)}-seed-{seed}.json"
    )
    write_atomic_json(cell_path, cast(YamlNode, cell.model_dump(mode="json")), staging)
    return cell_path


def _execute_real_emhi_methods(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> tuple[RecordCount, tuple[MethodName, ...]]:
    contract = _experiment_contract(loaded.values, experiment_name)
    dataset_name = campaign_dataset(loaded, experiment_name)
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
            score_path = with_technical_retry(
                loaded,
                partial(_materialize_detector_scores, loaded, repository, dataset_name, seed),
            )
            rank_path = with_technical_retry(
                loaded,
                partial(
                    _materialize_marginal_ranks,
                    loaded,
                    repository,
                    dataset_name,
                    seed,
                    score_path,
                ),
            )
            for method_name in supported:
                fit_path = with_technical_retry(
                    loaded,
                    partial(
                        _materialize_emhi_fit,
                        loaded,
                        repository,
                        dataset_name,
                        seed,
                        method_name,
                        score_path,
                        rank_path,
                    ),
                )
                with_technical_retry(
                    loaded,
                    partial(
                        _evaluate_emhi_seed_cell,
                        loaded,
                        repository,
                        experiment_name,
                        role,
                        method_name,
                        seed,
                        score_path,
                        rank_path,
                        fit_path,
                    ),
                )
                completed += 1
            for method_name in missing:
                with_technical_retry(
                    loaded,
                    partial(
                        _evaluate_comparator_seed_cell,
                        loaded,
                        repository,
                        experiment_name,
                        role,
                        method_name,
                        seed,
                        score_path,
                        rank_path,
                    ),
                )
                completed += 1
    return completed, ()


def sensitivity_base_specification(
    loaded: LoadedScientificConfiguration,
) -> tuple[ContextMethodName, CoalitionOrder, Boolean]:
    specification = _emhi_method_specification(MethodName.FULL_FEDCAMPAIGN_EMHI)
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
        nuisance_context_boundary_digest(loaded.values), (condition_digest,)
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
    campaign_rows, odi_values = _campaign_rows(loaded, scores, ranks, fit, campaigns, calibration)
    rows = tuple(cast(Mapping[str, YamlNode], row) for row in campaign_rows)
    detection_rate = (
        sum(cast(Boolean, row["global_detected_within_horizon"]) for row in rows) / len(rows)
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
        return method_artifact_stem(cast(MethodName, method_override))
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
        _preprocessing_paths(loaded, repository, dataset_name)
    )
    prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
    if not prepared.selected_client_ids:
        return ()
    split = DatasetSplitRecord.model_validate_json(split_path.read_bytes())
    partitions = BenignPartitionRecord.model_validate_json(partitions_path.read_bytes())
    campaigns = CampaignRegistryRecord.model_validate_json(campaigns_path.read_bytes())
    target_local_pfa = _local_pfa_target(loaded, experiment_name)
    conditions = sensitivity_conditions(loaded, base_context_method)
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(experiment_name)
    staging = layout.roots.outputs_root / "cache" / "staging"
    paths: list[Path] = []
    for seed in loaded.values.randomness.real_development_roots:
        score_path = with_technical_retry(
            loaded,
            partial(_materialize_detector_scores, loaded, repository, dataset_name, seed),
        )
        rank_path = with_technical_retry(
            loaded,
            partial(
                _materialize_marginal_ranks, loaded, repository, dataset_name, seed, score_path
            ),
        )
        base_fit_path = with_technical_retry(
            loaded,
            partial(
                _materialize_emhi_fit,
                loaded,
                repository,
                dataset_name,
                seed,
                MethodName.FULL_FEDCAMPAIGN_EMHI,
                score_path,
                rank_path,
            ),
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


def materialize_coalition_scalability_summaries(
    loaded: LoadedScientificConfiguration,
    repository: Path,
) -> tuple[Path, ...]:
    layout = build_artifact_layout(loaded, repository)
    root = layout.experiment_outputs_root(ExperimentName.COALITION_SCALABILITY)
    staging = layout.roots.outputs_root / "cache" / "staging"
    config = loaded.values
    maximum_order = config.study.maximum_coalition_order
    maximum_latency = config.materiality.reference_harness.p95_latency_maximum_seconds
    maximum_failure_rate = config.materiality.maximum_pooled_numerical_failure_rate
    paths: list[Path] = []
    for client_count in config.robustness.scalability_client_counts:
        coalitions = expected_scalability_coalitions(config, client_count)
        registered = registry_coalition_count(client_count, maximum_order)
        if coalitions != registered:
            raise ValueError("derived coalition count must match the registry coalition count")
        payload_bytes = application_payload_bytes_per_epoch(client_count)
        measurements: tuple[ScalabilityMeasurement, ...] = ()
        summary = (
            None
            if not measurements
            else summarize_scalability(
                client_count,
                measurements,
                maximum_latency,
                maximum_failure_rate,
            )
        )
        scored_rate = None
        if summary is not None and summary.median_server_latency_seconds > 0.0:
            scored_rate = throughput(coalitions, summary.median_server_latency_seconds)
        payload: YamlNode = {
            "client_count": client_count,
            "expected_coalitions": coalitions,
            "application_payload_bytes_per_epoch": payload_bytes,
            "median_server_latency_seconds": (
                None if summary is None else summary.median_server_latency_seconds
            ),
            "p95_server_latency_seconds": (
                None if summary is None else summary.p95_server_latency_seconds
            ),
            "numerical_failure_rate": None if summary is None else summary.numerical_failure_rate,
            "throughput": scored_rate,
            "latency_criterion_state": (
                SupportState.NOT_TESTED.value
                if summary is None
                else summary.latency_criterion_state.value
            ),
            "numerical_criterion_state": (
                SupportState.NOT_TESTED.value
                if summary is None
                else summary.numerical_criterion_state.value
            ),
            "state": ExperimentState.COMPLETED.value if summary is None else summary.state.value,
        }
        path = root / "metrics" / "aggregate" / f"k-{client_count}.json"
        write_atomic_json(path, payload, staging)
        paths.append(path)
    return tuple(paths)


def execute_campaign_experiment(
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
    if experiment_name is ExperimentName.COALITION_SCALABILITY:
        scalability_paths = materialize_coalition_scalability_summaries(loaded, repository)
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
            completed_cell_count=len(scalability_paths),
            detail="coalition-scalability derived summaries completed",
        )
    if experiment_name is ExperimentName.CONTEXT_AND_ESTIMATOR_SENSITIVITY:
        sensitivity_cells = materialize_context_and_estimator_sensitivity_cells(loaded, repository)
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
            completed_cell_count=len(sensitivity_cells),
            detail="one-factor sensitivity diagnostic cells completed",
        )
    if not contract.methods:
        prepared_path = _preprocessing_paths(
            loaded, repository, campaign_dataset(loaded, experiment_name)
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
    materialize_seed_statistics(loaded, repository, experiment_name)
    not_tested_primary = _materialize_not_tested_primary_holm_statistic(
        loaded, repository, experiment_name
    )
    _materialize_confirmatory_odi_inferences(
        loaded, repository, experiment_name, not_tested_primary is not None
    )
    if experiment_name is ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS:
        materialize_benign_common_mode_statistic(loaded, repository)
        materialize_benign_common_mode_count_stress_diagnostics(loaded, repository)
        materialize_benign_common_mode_positive_power_measurement(loaded, repository)
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
