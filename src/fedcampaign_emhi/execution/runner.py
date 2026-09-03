from pathlib import Path
from typing import cast

from fedcampaign_emhi.artifacts.records import PlanArtifactRecord, PlannedExperimentRecord
from fedcampaign_emhi.artifacts.storage import build_artifact_layout, write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import ExperimentName, OverwritePolicy
from fedcampaign_emhi.execution.planning import plan_experiments
from fedcampaign_emhi.experiments.campaigns import (
    ExperimentExecutionResult,
    execute_campaign_experiment,
)
from fedcampaign_emhi.experiments.registry import RESUME_SEQUENCE, assert_known_experiment
from fedcampaign_emhi.runtime import log_stage


@log_stage("execution.runner")
def execute_experiment(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    overwrite_policy: OverwritePolicy,
) -> ExperimentExecutionResult:
    assert_known_experiment(loaded.values, experiment_name)
    return execute_campaign_experiment(loaded, repository, experiment_name, overwrite_policy)


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
        destination,
        cast(YamlNode, record.model_dump(mode="json")),
        staging,
    )
    return destination
