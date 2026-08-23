from dataclasses import dataclass, replace
from pathlib import Path

from pydantic import ValidationError

from fedcampaign_emhi.artifacts.paths import build_artifact_layout
from fedcampaign_emhi.artifacts.records import ExperimentRunRecord
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import (
    ArtifactLifecycleState,
    ExecutionRole,
    ExperimentName,
    ExperimentState,
)
from fedcampaign_emhi.domain.types import SeedCount
from fedcampaign_emhi.execution.planning import plan_experiments


@dataclass(frozen=True)
class ExperimentStatus:
    experiment_name: ExperimentName
    state: ExperimentState
    lifecycle_state: ArtifactLifecycleState
    development_seed_count: SeedCount
    confirmatory_seed_count: SeedCount


def _run_record_state(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
) -> tuple[ExperimentState, ArtifactLifecycleState]:
    layout = build_artifact_layout(loaded, repository)
    path = (
        layout.experiment_outputs_root(experiment_name)
        / "provenance"
        / "dependencies"
        / "run-record.json"
    )
    if not path.is_file():
        return ExperimentState.NOT_STARTED, ArtifactLifecycleState.MISSING
    try:
        record = ExperimentRunRecord.model_validate_json(path.read_bytes())
    except (ValidationError, ValueError):
        return ExperimentState.INVALID, ArtifactLifecycleState.MALFORMED
    if record.material_digest != loaded.material_digest:
        return ExperimentState.BLOCKED, ArtifactLifecycleState.STALE
    lifecycle = (
        ArtifactLifecycleState.VALID
        if record.state is ExperimentState.COMPLETED
        else ArtifactLifecycleState.INCOMPLETE
    )
    if record.state is ExperimentState.FAILED:
        lifecycle = ArtifactLifecycleState.FAILED
    return record.state, lifecycle


def project_status(
    loaded: LoadedScientificConfiguration, repository: Path
) -> tuple[ExperimentStatus, ...]:
    statuses: list[ExperimentStatus] = []
    for planned in plan_experiments(loaded):
        existing_index = next(
            (
                index
                for index, item in enumerate(statuses)
                if item.experiment_name is planned.experiment_name
            ),
            None,
        )
        if existing_index is None:
            state, lifecycle = _run_record_state(
                loaded, repository, planned.experiment_name
            )
            development = planned.seed_count
            confirmatory = 0
            if planned.execution_role is ExecutionRole.CONFIRMATORY:
                development = 0
                confirmatory = planned.seed_count
            statuses.append(
                ExperimentStatus(
                    experiment_name=planned.experiment_name,
                    state=state,
                    lifecycle_state=lifecycle,
                    development_seed_count=development,
                    confirmatory_seed_count=confirmatory,
                )
            )
            continue
        current = statuses[existing_index]
        if planned.execution_role is ExecutionRole.CONFIRMATORY:
            statuses[existing_index] = replace(current, confirmatory_seed_count=planned.seed_count)
        else:
            statuses[existing_index] = replace(
                current,
                development_seed_count=max(current.development_seed_count, planned.seed_count),
            )
    return tuple(statuses)
