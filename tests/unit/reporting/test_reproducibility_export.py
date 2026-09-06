import json
from pathlib import Path

from fedcampaign_emhi.config.loading import load_production_configuration
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.reporting.export import export_reproducibility


def _exported_map(root: Path, paths: tuple[Path, ...]) -> dict[str, Path]:
    return {path.relative_to(root).as_posix(): path for path in paths}


def test_reproducibility_export_includes_plan_environment_and_identity_sources(
    production_configuration: LoadedScientificConfiguration, tmp_path: Path
) -> None:
    paths = export_reproducibility(production_configuration, tmp_path, ())

    names = {path.name for path in paths}
    assert {
        "environment-identity.json",
        "plan-snapshot.json",
        "experiment-completion-metadata.json",
        "preprocessing-identity.json",
    } <= names

    plan = json.loads(
        (
            tmp_path
            / "results"
            / "project_summary"
            / "reproducibility"
            / "execution"
            / "plan-snapshot.json"
        ).read_text(encoding="utf-8")
    )
    assert plan["material_configuration_digest"] == production_configuration.material_digest
    assert len(plan["planned_experiments"]) == 30

    environment = json.loads(
        (
            tmp_path
            / "results"
            / "project_summary"
            / "reproducibility"
            / "execution"
            / "environment-identity.json"
        ).read_text(encoding="utf-8")
    )
    assert environment["operating_system"]
    assert environment["python_version"]

    identities = json.loads(
        (
            tmp_path
            / "results"
            / "project_summary"
            / "reproducibility"
            / "datasets"
            / "preprocessing-identity.json"
        ).read_text(encoding="utf-8")
    )
    assert {entry["dataset_name"] for entry in identities["datasets"]} == {
        "TON_IoT Network",
        "Edge-IIoTset",
    }
    assert all(entry["layers"] == [] for entry in identities["datasets"])


def test_reproducibility_export_is_deterministic_across_repositories(
    tmp_path: Path,
) -> None:
    loaded = load_production_configuration()
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first = export_reproducibility(loaded, first_root, ())
    second = export_reproducibility(loaded, second_root, ())

    first_map = _exported_map(first_root, first)
    second_map = _exported_map(second_root, second)
    assert set(first_map) == set(second_map)
    for relative, first_path in first_map.items():
        assert first_path.read_bytes() == second_map[relative].read_bytes()
