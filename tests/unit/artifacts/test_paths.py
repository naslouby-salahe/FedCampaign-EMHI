from pathlib import Path

from fedcampaign_emhi.artifacts.dependencies import descendant_ids
from fedcampaign_emhi.artifacts.paths import build_artifact_layout
from fedcampaign_emhi.artifacts.storage import payload_digest, write_atomic_json
from fedcampaign_emhi.artifacts.validation import inspect_artifact, may_reuse
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.domain.types import ArtifactDependencyNode


def test_required_layout_contains_distinct_outputs_and_results(
    production_configuration: LoadedScientificConfiguration, repo_root: Path
) -> None:
    layout = build_artifact_layout(production_configuration, repo_root)
    assert layout.roots.outputs_root != layout.roots.results_root
    required = layout.required_directories()
    assert layout.roots.outputs_root / "cache" / "staging" in required


def test_atomic_json_round_trip_and_reuse(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    destination = tmp_path / "artifact.json"
    payload = {"artifact_id": "example", "value": 1}
    digest = write_atomic_json(destination, payload, staging)
    assert payload_digest(payload) == digest
    assert destination.is_file()
    assert not list(staging.glob("*.partial"))


def test_descendant_invalidation_is_selective() -> None:
    graph = (
        ArtifactDependencyNode("raw", "a" * 64, ()),
        ArtifactDependencyNode("prepared", "b" * 64, ("raw",)),
        ArtifactDependencyNode("scores", "c" * 64, ("prepared",)),
        ArtifactDependencyNode("sibling", "d" * 64, ()),
    )
    assert descendant_ids(graph, ("prepared",)) == ("scores",)
    assert "sibling" not in descendant_ids(graph, ("prepared",))


def test_missing_artifact_cannot_be_reused(tmp_path: Path) -> None:
    inspection = inspect_artifact(tmp_path / "absent.json", None, None)
    assert may_reuse(inspection) is False
