from pathlib import Path

from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import (
    ExecutionRole,
    ExperimentName,
    ExperimentState,
    MethodName,
    OverwritePolicy,
)
from fedcampaign_emhi.domain.types import FalseAlarmRate, RecordCount, SeedValue
from fedcampaign_emhi.execution.real_data import execute_emhi_method_seed_cell
from fedcampaign_emhi.execution.runner import (
    ExperimentExecutionResult,
    _existing_completed_run,
    _execute_synthetic_module_validation,
    _experiment_contract,
    _materialize_detector_scores,
    _materialize_full_emhi_fit,
    _materialize_marginal_ranks,
    _preprocessing_paths,
    _required_preprocessing_artifacts,
    publish_experiment_run_record,
    validate_scientific_implementation_registry,
)


EMHI_OPERATIONAL_METHODS: frozenset[MethodName] = frozenset(
    {
        MethodName.FULL_FEDCAMPAIGN_EMHI,
        MethodName.EXCLUSION_MATCHED_ORDER_ONE_EMHI,
        MethodName.EXCLUSION_MATCHED_ORDER_AT_MOST_TWO_EMHI,
    }
)


def _role_roots(
    loaded: LoadedScientificConfiguration,
    execution_role: ExecutionRole,
) -> tuple[SeedValue, ...]:
    if execution_role is ExecutionRole.CONFIRMATORY:
        return loaded.values.randomness.real_confirmatory_roots
    return loaded.values.randomness.real_development_roots


def _local_target(
    loaded: LoadedScientificConfiguration,
    experiment_name: ExperimentName,
) -> FalseAlarmRate:
    if experiment_name is ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE:
        return loaded.values.local_policy.strong_horizon_pfa_target
    return loaded.values.local_policy.primary_horizon_pfa_target


def _execute_emhi_cells(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> tuple[RecordCount, tuple[MethodName, ...]]:
    contract = _experiment_contract(loaded.values, experiment_name)
    supported_methods = tuple(method for method in contract.methods if method in EMHI_OPERATIONAL_METHODS)
    if not supported_methods:
        return 0, contract.methods
    dataset_name = (
        loaded.values.datasets.secondary.name
        if experiment_name is ExperimentName.SECONDARY_CONTROLLED_TRACE_GENERALIZATION
        else loaded.values.datasets.primary.name
    )
    _, _, split_path, partitions_path, campaigns_path = _preprocessing_paths(
        loaded,
        repository,
        dataset_name,
    )
    target_local_pfa = _local_target(loaded, experiment_name)
    completed = 0
    for execution_role in contract.execution_roles:
        for seed in _role_roots(loaded, execution_role):
            score_path = _materialize_detector_scores(loaded, repository, dataset_name, seed)
            rank_path = _materialize_marginal_ranks(
                loaded,
                repository,
                dataset_name,
                seed,
                score_path,
            )
            fit_path = _materialize_full_emhi_fit(
                loaded,
                repository,
                dataset_name,
                seed,
                score_path,
                rank_path,
            )
            for method_name in supported_methods:
                result = execute_emhi_method_seed_cell(
                    loaded=loaded,
                    repository=repository,
                    experiment_name=experiment_name,
                    execution_role=execution_role,
                    method_name=method_name,
                    seed=seed,
                    score_path=score_path,
                    rank_path=rank_path,
                    fit_path=fit_path,
                    split_path=split_path,
                    partitions_path=partitions_path,
                    campaigns_path=campaigns_path,
                    target_local_pfa=target_local_pfa,
                )
                if result.state is ExperimentState.COMPLETED:
                    completed += 1
    missing_methods = tuple(method for method in contract.methods if method not in EMHI_OPERATIONAL_METHODS)
    return completed, missing_methods


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
            detail="synthetic experiment producer remains incomplete",
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
    completed_cells, missing_methods = _execute_emhi_cells(
        loaded,
        repository,
        experiment_name,
    )
    fully_implemented = bool(contract.methods) and not missing_methods
    state = ExperimentState.COMPLETED if fully_implemented else ExperimentState.BLOCKED
    run_path = publish_experiment_run_record(
        loaded,
        repository,
        experiment_name,
        overwrite_policy,
        state,
    )
    detail = (
        "all configured EMHI operational cells completed"
        if fully_implemented
        else "remaining configured methods or scientific conditions are not yet implemented"
    )
    return ExperimentExecutionResult(
        experiment_name=experiment_name,
        state=state,
        run_record_path=run_path,
        completed_cell_count=completed_cells,
        detail=detail,
    )
