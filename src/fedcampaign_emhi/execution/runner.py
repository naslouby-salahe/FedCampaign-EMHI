from pathlib import Path

from fedcampaign_emhi.analysis.results import reconcile_project_holm_families
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import ExperimentName, ExperimentState, OverwritePolicy
from fedcampaign_emhi.experiments.execution import ExperimentExecutionResult
from fedcampaign_emhi.experiments.orchestration import execute_campaign_experiment
from fedcampaign_emhi.experiments.registry import assert_known_experiment
from fedcampaign_emhi.runtime import log_stage


@log_stage("execution.runner")
def execute_experiment(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    overwrite_policy: OverwritePolicy,
) -> ExperimentExecutionResult:
    assert_known_experiment(loaded.values, experiment_name)
    result = execute_campaign_experiment(loaded, repository, experiment_name, overwrite_policy)
    if result.state is ExperimentState.COMPLETED:
        reconcile_project_holm_families(loaded, repository)
    return result
