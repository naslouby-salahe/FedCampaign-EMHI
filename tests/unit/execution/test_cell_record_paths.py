from pathlib import Path

from fedcampaign_emhi.artifacts.storage import write_atomic_json
from fedcampaign_emhi.experiments.execution import cell_record_paths


def test_cell_record_paths_exclude_run_record(tmp_path: Path) -> None:
    dependencies = tmp_path / "provenance" / "dependencies"
    write_atomic_json(
        dependencies / "run-record.json",
        {"state": "Completed"},
        tmp_path / "staging",
    )
    write_atomic_json(dependencies / "cell-a.json", {"state": "Completed"}, tmp_path / "staging")
    write_atomic_json(dependencies / "cell-b.json", {"state": "Completed"}, tmp_path / "staging")

    paths = cell_record_paths(tmp_path)

    assert [path.name for path in paths] == ["cell-a.json", "cell-b.json"]


def test_cell_record_paths_empty_without_dependency_directory(tmp_path: Path) -> None:
    assert cell_record_paths(tmp_path / "missing") == ()
