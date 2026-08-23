from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from fedcampaign_emhi.analysis.claims import evaluate_strict_odi
from fedcampaign_emhi.analysis.statistics import paired_difference
from fedcampaign_emhi.analysis.summaries import build_seed_summary
from fedcampaign_emhi.artifacts.paths import build_artifact_layout
from fedcampaign_emhi.artifacts.provenance import material_fingerprint
from fedcampaign_emhi.artifacts.records import (
    CompletionRecord,
    ExperimentRunRecord,
    PlanArtifactRecord,
    PlannedExperimentRecord,
    ScientificCellRecord,
)
from fedcampaign_emhi.artifacts.storage import write_atomic_json
from fedcampaign_emhi.comparators.composition import select_strongest_comparator
from fedcampaign_emhi.comparators.conditional_hofd import hofd_atom_rows
from fedcampaign_emhi.comparators.conditional_log_linear import log_linear_design_column_count
from fedcampaign_emhi.comparators.connected_information import uniform_probability_table
from fedcampaign_emhi.comparators.contracts import comparator_method_contracts
from fedcampaign_emhi.comparators.d_vine import lexicographic_vine_order
from fedcampaign_emhi.comparators.fedavg_autoencoder import fedavg_weighted_mean
from fedcampaign_emhi.comparators.global_factor_residual import selected_factor_rank
from fedcampaign_emhi.comparators.lancaster import lancaster_triple_moment
from fedcampaign_emhi.comparators.multistream_cusum import next_cusum_state
from fedcampaign_emhi.comparators.pair_dependence import pair_dependence_moment
from fedcampaign_emhi.comparators.rank_fusion import mean_rank_fusion
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.datasets.preprocessing import epoch_feature_vector
from fedcampaign_emhi.detection.detector_assignment import assign_detector_families
from fedcampaign_emhi.detection.fitting import score_autoencoder, score_isolation_forest, score_one_class_svm
from fedcampaign_emhi.domain.enums import (
    ExecutionRole,
    ExperimentName,
    ExperimentState,
    OverwritePolicy,
)
from fedcampaign_emhi.domain.types import ComponentName, RecordCount, ResumeStep, RuntimeSeconds
from fedcampaign_emhi.evaluation.scalability import summarize_scalability
from fedcampaign_emhi.evaluation.smoke_gate import run_synthetic_module_validation
from fedcampaign_emhi.evaluation.validation import campaign_record_state
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE, plan_experiments
from fedcampaign_emhi.experiments.ablations import (
    enumerate_exclusion_mechanism_ablation,
    enumerate_purification_and_order_ablation,
)
from fedcampaign_emhi.experiments.benign_robustness import enumerate_benign_common_mode_plan
from fedcampaign_emhi.experiments.boundaries import (
    enumerate_dropout_boundary_plan,
    enumerate_outside_contamination_plan,
)
from fedcampaign_emhi.experiments.definitions import experiment_registry
from fedcampaign_emhi.experiments.primary_odi import enumerate_primary_strict_odi_plan
from fedcampaign_emhi.experiments.scalability import enumerate_scalability_plan
from fedcampaign_emhi.experiments.secondary_generalization import (
    enumerate_secondary_generalization_plan,
)
from fedcampaign_emhi.experiments.sensitivity import enumerate_sensitivity_cells
from fedcampaign_emhi.experiments.strong_local import enumerate_strong_local_policy_plan
from fedcampaign_emhi.experiments.validation import assert_known_experiment
from fedcampaign_emhi.synthetic.common_mode import generate_common_mode_scores
from fedcampaign_emhi.synthetic.controlled_campaigns import apply_marginal_score_shift
from fedcampaign_emhi.synthetic.robustness import availability_mask
from fedcampaign_emhi.synthetic.self_explanation import enumerate_self_exclusion_grid
from fedcampaign_emhi.synthetic.validation import validate_synthetic_generators


@dataclass(frozen=True)
class ExperimentExecutionResult:
    experiment_name: ExperimentName
    state: ExperimentState
    run_record_path: Path
    completed_cell_count: RecordCount
    detail: ComponentName


_IMPLEMENTATION_PROBES = (
    evaluate_strict_odi,
    paired_difference,
    build_seed_summary,
    select_strongest_comparator,
    hofd_atom_rows,
    log_linear_design_column_count,
    uniform_probability_table,
    lexicographic_vine_order,
    fedavg_weighted_mean,
    selected_factor_rank,
    lancaster_triple_moment,
    next_cusum_state,
    pair_dependence_moment,
    mean_rank_fusion,
    epoch_feature_vector,
    assign_detector_families,
    score_autoencoder,
    score_isolation_forest,
    score_one_class_svm,
    summarize_scalability,
    campaign_record_state,
    generate_common_mode_scores,
    apply_marginal_score_shift,
    availability_mask,
    enumerate_self_exclusion_grid,
)


def resume_sequence() -> tuple[ResumeStep, ...]:
    return RESUME_SEQUENCE


def implementation_probe_names() -> tuple[ComponentName, ...]:
    return tuple(f"{probe.__module__}.{probe.__name__}" for probe in _IMPLEMENTATION_PROBES)


def validate_scientific_implementation_registry(
    config: ScientificConfig, experiment_name: ExperimentName
) -> tuple[ComponentName, ...]:
    assert_known_experiment(config, experiment_name)
    contracts = comparator_method_contracts()
    if len({contract.method_name for contract in contracts}) != len(contracts):
        raise ValueError("comparator method contracts must have unique method ownership")
    if experiment_name is ExperimentName.SELF_EXPLANATION_EXCLUSION_VALIDATION:
        enumerate_self_exclusion_grid(config)
    elif experiment_name is ExperimentName.PRIMARY_STRICT_ODI_EVALUATION:
        enumerate_primary_strict_odi_plan(config)
    elif experiment_name is ExperimentName.EXCLUSION_MECHANISM_ABLATION:
        enumerate_exclusion_mechanism_ablation(config)
    elif experiment_name is ExperimentName.PURIFICATION_AND_ORDER_ABLATION:
        enumerate_purification_and_order_ablation(config)
    elif experiment_name is ExperimentName.CONTEXT_AND_ESTIMATOR_SENSITIVITY:
        enumerate_sensitivity_cells(config)
    elif experiment_name is ExperimentName.BENIGN_COMMON_MODE_ROBUSTNESS:
        enumerate_benign_common_mode_plan(config)
    elif experiment_name is ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE:
        enumerate_strong_local_policy_plan(config)
    elif experiment_name is ExperimentName.SECONDARY_CONTROLLED_TRACE_GENERALIZATION:
        enumerate_secondary_generalization_plan(config)
    elif experiment_name is ExperimentName.OUTSIDE_CAMPAIGN_CONTAMINATION_BOUNDARY:
        enumerate_outside_contamination_plan(config)
    elif experiment_name is ExperimentName.CLIENT_DROPOUT_AND_CONTEXT_SPARSITY_BOUNDARY:
        enumerate_dropout_boundary_plan(config)
    elif experiment_name is ExperimentName.COALITION_SCALABILITY:
        enumerate_scalability_plan(config)
    probes = implementation_probe_names()
    if not probes:
        raise ValueError("scientific implementation registry is empty")
    return probes


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
    write_atomic_json(destination, record.model_dump(mode="json"), staging)
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
    cell_root = path.parent
    completed_cells = tuple(child for child in cell_root.glob("cell-*.json") if child.is_file())
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
    relative_output = str(diagnostic_path.relative_to(repository))
    completion = CompletionRecord(
        state=state,
        mandatory_output_paths=(relative_output,),
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
    write_atomic_json(cell_path, cell.model_dump(mode="json"), staging)
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


def _required_preprocessing_artifacts(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> tuple[Path, ...]:
    contract = next(
        contract
        for contract in experiment_registry(loaded.values)
        if contract.experiment_name is experiment_name
    )
    if not contract.uses_real_seeds:
        return ()
    layout = build_artifact_layout(loaded, repository)
    root = layout.roots.outputs_root / "preprocessing"
    dataset_name = (
        loaded.values.datasets.secondary.name
        if experiment_name is ExperimentName.SECONDARY_CONTROLLED_TRACE_GENERALIZATION
        else loaded.values.datasets.primary.name
    )
    stem = dataset_name.value.replace(" ", "_")
    return (
        root / "inventories" / f"{stem}.json",
        root / "prepared" / f"{stem}.json",
        root / "splits" / f"{stem}.json",
        root / "metadata" / f"{stem}-benign-partitions.json",
        root / "metadata" / f"{stem}-campaign-registry.json",
    )


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
        detail="scientific producer has unresolved execution cells",
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
    write_atomic_json(destination, record.model_dump(mode="json"), staging)
    return destination
