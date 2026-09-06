from pathlib import Path
from typing import cast

from fedcampaign_emhi.artifacts.records import CompletionRecord, ScientificCellRecord
from fedcampaign_emhi.artifacts.storage import build_artifact_layout, write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import (
    ExecutionRole,
    ExperimentName,
    ExperimentState,
    MethodName,
)
from fedcampaign_emhi.execution.status import project_status


def _write_cell(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    experiment_name: ExperimentName,
    stem: str,
    state: ExperimentState,
) -> None:
    layout = build_artifact_layout(loaded, repository)
    cell = ScientificCellRecord(
        experiment_name=experiment_name,
        execution_role=ExecutionRole.DEVELOPMENT,
        semantic_cell_path=stem,
        method_name=MethodName.FULL_FEDCAMPAIGN_EMHI,
        seed=1,
        state=state,
        material_digest=loaded.material_digest,
        selected_client_ids=(),
        upstream_artifact_ids=(),
        dependency_fingerprint="d" * 64,
        runtime_seconds=0.0,
        peak_rss_bytes=0,
        application_payload_bytes=0,
        completion_record=CompletionRecord(
            state=state,
            mandatory_output_paths=(),
            mandatory_output_hashes=(),
        ),
    )
    path = (
        layout.experiment_outputs_root(experiment_name)
        / "provenance"
        / "dependencies"
        / f"cell-{stem}.json"
    )
    write_atomic_json(
        path,
        cast(YamlNode, cell.model_dump(mode="json")),
        repository / "outputs" / "cache" / "staging",
    )


def test_project_status_counts_completed_failed_and_invalid_cells(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    experiment = ExperimentName.STRONG_LOCAL_POLICY_CHALLENGE
    _write_cell(
        production_configuration, tmp_path, experiment, "completed-a", ExperimentState.COMPLETED
    )
    _write_cell(
        production_configuration, tmp_path, experiment, "completed-b", ExperimentState.COMPLETED
    )
    _write_cell(production_configuration, tmp_path, experiment, "failed", ExperimentState.FAILED)
    _write_cell(production_configuration, tmp_path, experiment, "invalid", ExperimentState.INVALID)

    statuses = project_status(production_configuration, tmp_path)
    status = next(item for item in statuses if item.experiment_name is experiment)

    assert status.completed_cell_count == 2
    assert status.failed_cell_count == 1
    assert status.invalid_cell_count == 1
