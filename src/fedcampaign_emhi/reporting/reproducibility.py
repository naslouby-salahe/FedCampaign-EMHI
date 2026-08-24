import platform
import sys
from pathlib import Path
from typing import cast

from fedcampaign_emhi.artifacts.paths import build_artifact_layout
from fedcampaign_emhi.artifacts.storage import file_sha256, write_atomic_json
from fedcampaign_emhi.config.schema import LoadedScientificConfiguration
from fedcampaign_emhi.config.validation import YamlNode
from fedcampaign_emhi.domain.enums import ExperimentName


def export_reproducibility(
    loaded: LoadedScientificConfiguration,
    repository: Path,
    completed_experiments: tuple[ExperimentName, ...],
) -> tuple[Path, ...]:
    layout = build_artifact_layout(loaded, repository)
    root = layout.roots.results_root / "project_summary" / "reproducibility"
    staging = layout.roots.outputs_root / "cache" / "staging"
    configuration_path = root / "configuration" / "scientific-configuration.json"
    dataset_path = root / "datasets" / "dataset-configuration.json"
    seed_path = root / "seeds" / "seed-configuration.json"
    software_path = root / "software" / "software-identity.json"
    execution_path = root / "execution" / "completed-experiments.json"
    write_atomic_json(
        configuration_path,
        cast(YamlNode, loaded.values.model_dump(mode="json")),
        staging,
    )
    write_atomic_json(
        dataset_path,
        cast(YamlNode, loaded.values.datasets.model_dump(mode="json")),
        staging,
    )
    write_atomic_json(
        seed_path,
        cast(YamlNode, loaded.values.randomness.model_dump(mode="json")),
        staging,
    )
    lock_path = repository / "uv.lock"
    software_payload: YamlNode = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "uv_lock_sha256": file_sha256(lock_path) if lock_path.is_file() else None,
    }
    write_atomic_json(software_path, software_payload, staging)
    execution_payload: YamlNode = {
        "material_configuration_digest": loaded.material_digest,
        "completed_experiments": [experiment.value for experiment in completed_experiments],
    }
    write_atomic_json(execution_path, execution_payload, staging)
    return (
        configuration_path,
        dataset_path,
        seed_path,
        software_path,
        execution_path,
    )
