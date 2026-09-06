from dataclasses import dataclass, replace
from pathlib import Path

from pydantic import ValidationError

from fedcampaign_emhi.artifacts.records import ExperimentRunRecord, ScientificCellRecord
from fedcampaign_emhi.artifacts.storage import build_artifact_layout, file_sha256
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.enums import (
    ArtifactLifecycleState,
    ExecutionRole,
    ExperimentName,
    ExperimentState,
)
from fedcampaign_emhi.domain.types import RecordCount, SeedCount
from fedcampaign_emhi.execution.planning import plan_experiments
from fedcampaign_emhi.experiments.execution import cell_record_paths
from fedcampaign_emhi.runtime import log_stage


@dataclass(frozen=True)
class ExperimentStatus:
    experiment_name: ExperimentName
    state: ExperimentState
    lifecycle_state: ArtifactLifecycleState
    development_seed_count: SeedCount
    confirmatory_seed_count: SeedCount
    completed_cell_count: RecordCount
    failed_cell_count: RecordCount
    invalid_cell_count: RecordCount


def _cell_state_counts(cell_paths: tuple[Path, ...]) -> tuple[RecordCount, ...]:
    completed = 0
    failed = 0
    invalid = 0
    for cell_path in cell_paths:
        try:
            cell = ScientificCellRecord.model_validate_json(cell_path.read_bytes())
        except (ValidationError, ValueError):
            invalid += 1
            continue
        if cell.state is ExperimentState.COMPLETED:
            completed += 1
        elif cell.state is ExperimentState.FAILED:
            failed += 1
        else:
            invalid += 1
    return completed, failed, invalid


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
    cell_paths = cell_record_paths(path.parent)
    if not cell_paths:
        return ExperimentState.BLOCKED, ArtifactLifecycleState.INCOMPLETE
    for cell_path in cell_paths:
        failure = _cell_validation_failure(loaded, repository, cell_path)
        if failure is not None:
            return failure
    lifecycle = (
        ArtifactLifecycleState.VALID
        if record.state is ExperimentState.COMPLETED
        else ArtifactLifecycleState.INCOMPLETE
    )
    if record.state is ExperimentState.FAILED:
        lifecycle = ArtifactLifecycleState.FAILED
    return record.state, lifecycle


def _cell_validation_failure(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    cell_path: Path,
) -> tuple[ExperimentState, ArtifactLifecycleState] | None:
    try:
        cell = ScientificCellRecord.model_validate_json(cell_path.read_bytes())
    except (ValidationError, ValueError):
        return ExperimentState.INVALID, ArtifactLifecycleState.MALFORMED
    if cell.material_digest != loaded.material_digest:
        return ExperimentState.BLOCKED, ArtifactLifecycleState.STALE
    if cell.state is not ExperimentState.COMPLETED:
        return cell.state, ArtifactLifecycleState.INCOMPLETE
    if len(cell.completion_record.mandatory_output_paths) != len(
        cell.completion_record.mandatory_output_hashes
    ):
        return ExperimentState.INVALID, ArtifactLifecycleState.INCOMPLETE
    for relative_path, expected_hash in zip(
        cell.completion_record.mandatory_output_paths,
        cell.completion_record.mandatory_output_hashes,
        strict=True,
    ):
        output_path = repository / relative_path
        if not output_path.is_file() or file_sha256(output_path) != expected_hash:
            return ExperimentState.BLOCKED, ArtifactLifecycleState.STALE
    return None


@log_stage("execution.status")
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
            state, lifecycle = _run_record_state(loaded, repository, planned.experiment_name)
            layout = build_artifact_layout(loaded, repository)
            cell_paths = cell_record_paths(layout.experiment_outputs_root(planned.experiment_name))
            completed, failed, invalid = _cell_state_counts(cell_paths)
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
                    completed_cell_count=completed,
                    failed_cell_count=failed,
                    invalid_cell_count=invalid,
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
