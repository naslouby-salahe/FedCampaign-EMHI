from collections.abc import Callable

import typer

from fedcampaign_emhi.artifacts.paths import build_artifact_layout
from fedcampaign_emhi.config.loading import production_configuration_context
from fedcampaign_emhi.datasets.inventory import configured_raw_directory, discover_raw_paths
from fedcampaign_emhi.domain.enums import DatasetName
from fedcampaign_emhi.runtime.monitoring import assess_implementation_readiness


def doctor_command() -> None:
    emit: Callable[[str], None] = typer.echo
    repository, loaded = production_configuration_context()
    readiness = assess_implementation_readiness(loaded, repository)
    layout = build_artifact_layout(loaded, repository)
    primary_raw = configured_raw_directory(loaded, DatasetName.TON_IOT_NETWORK, repository)
    secondary_raw = configured_raw_directory(loaded, DatasetName.EDGE_IIOTSET, repository)
    primary_files = discover_raw_paths(primary_raw)
    secondary_files = discover_raw_paths(secondary_raw)
    missing_directories = [path for path in layout.required_directories() if not path.exists()]
    raw_inventory_executable = primary_raw.exists() and secondary_raw.exists()
    emit(f"repository={repository}")
    emit(f"configuration={loaded.source_path}")
    emit(f"material_digest={readiness.material_digest}")
    emit(f"production_configuration_valid={readiness.production_configuration_valid}")
    emit(f"raw_inventory_executable={raw_inventory_executable}")
    emit(f"unspecified_scientific_choice_count={readiness.unspecified_scientific_choice_count}")
    emit(f"primary_raw_directory={primary_raw}")
    emit(f"primary_raw_file_count={len(primary_files)}")
    emit(f"secondary_raw_directory={secondary_raw}")
    emit(f"secondary_raw_file_count={len(secondary_files)}")
    emit(f"missing_artifact_directories={len(missing_directories)}")
    emit("next_action=fedcampaign preprocess")
