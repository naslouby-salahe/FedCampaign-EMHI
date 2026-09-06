from pathlib import Path

from fedcampaign_emhi.artifacts.records import (
    ExperimentRunRecord,
    PreparedDatasetRecord,
    ScientificCellRecord,
)
from fedcampaign_emhi.artifacts.storage import (
    file_sha256,
)
from fedcampaign_emhi.comparators.runtime import (
    validate_comparator_runtime_contracts,
)
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration, ScientificConfig
from fedcampaign_emhi.domain.enums import (
    ExperimentName,
    ExperimentState,
    OverwritePolicy,
)
from fedcampaign_emhi.domain.types import (
    Boolean,
    ConfigurationDigest,
)
from fedcampaign_emhi.experiments.coalition_scalability import (
    materialize_coalition_scalability_summaries,
)
from fedcampaign_emhi.experiments.execution import (
    ExperimentExecutionResult,
    campaign_dataset,
    campaigns_logger,
    experiment_contract,
    implementation_digest,
    publish_experiment_run_record,
    run_record_path,
)
from fedcampaign_emhi.experiments.registry import (
    assert_known_experiment,
)
from fedcampaign_emhi.experiments.seed_evaluation import (
    execute_real_emhi_methods,
    materialize_context_and_estimator_sensitivity_cells,
    materialize_not_tested_real_cell,
    role_seeds,
)
from fedcampaign_emhi.experiments.seed_materialization import (
    preprocessing_paths,
    required_preprocessing_artifacts,
)
from fedcampaign_emhi.experiments.seed_statistics import (
    materialize_benign_common_mode_count_stress_diagnostics,
    materialize_benign_common_mode_positive_power_measurement,
    materialize_benign_common_mode_statistic,
    materialize_confirmatory_odi_inferences,
    materialize_not_tested_primary_holm_statistic,
    materialize_seed_statistics,
)
from fedcampaign_emhi.experiments.synthetic_execution import (
    execute_synthetic_experiment,
    execute_synthetic_module_validation,
)


def validate_scientific_implementation_registry(
    config: ScientificConfig, experiment_name: ExperimentName
) -> None:
    validate_comparator_runtime_contracts(config)
    assert_known_experiment(config, experiment_name)
    contract = experiment_contract(config, experiment_name)
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
    path = run_record_path(loaded, repository, experiment_name)
    if not path.is_file():
        return None
    try:
        record = ExperimentRunRecord.model_validate_json(path.read_bytes())
    except ValueError:
        return None
    if (
        record.material_digest != loaded.material_digest
        or record.implementation_digest != implementation_digest(repository)
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


def execute_campaign_experiment(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    overwrite_policy: OverwritePolicy,
) -> ExperimentExecutionResult:
    campaigns_logger().info(
        "experiment_started experiment=%s overwrite_policy=%s",
        experiment_name.value,
        overwrite_policy.value,
    )
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
        return execute_synthetic_module_validation(loaded, repository, overwrite_policy)
    contract = experiment_contract(loaded.values, experiment_name)
    if not contract.uses_real_seeds:
        return execute_synthetic_experiment(
            loaded,
            repository,
            experiment_name,
            overwrite_policy,
        )
    required = required_preprocessing_artifacts(loaded, repository, experiment_name)
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
        prepared_path = preprocessing_paths(
            loaded, repository, campaign_dataset(loaded, experiment_name)
        )[1]
        prepared = PreparedDatasetRecord.model_validate_json(prepared_path.read_bytes())
        completed = 0
        for role in contract.execution_roles:
            for seed in role_seeds(loaded, role):
                materialize_not_tested_real_cell(
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
    completed, _terminal_method_gaps = execute_real_emhi_methods(
        loaded,
        repository,
        experiment_name,
    )
    materialize_seed_statistics(loaded, repository, experiment_name)
    not_tested_primary = materialize_not_tested_primary_holm_statistic(
        loaded, repository, experiment_name
    )
    materialize_confirmatory_odi_inferences(
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
