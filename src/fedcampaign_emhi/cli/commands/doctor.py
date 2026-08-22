from collections.abc import Callable

import typer

from fedcampaign_emhi.artifacts.paths import build_artifact_layout
from fedcampaign_emhi.config.loading import load_production_configuration, repository_root
from fedcampaign_emhi.datasets.inventory import configured_raw_directory, discover_raw_paths
from fedcampaign_emhi.domain.enums import DatasetName
from fedcampaign_emhi.execution.status import module_contracts
from fedcampaign_emhi.reporting.figures import figures_contract
from fedcampaign_emhi.reporting.reproducibility import reproducibility_contract
from fedcampaign_emhi.reporting.tables import tables_contract
from fedcampaign_emhi.runtime.monitoring import assess_implementation_readiness


def doctor_command() -> None:
    emit: Callable[[str], None] = typer.echo
    repository = repository_root()
    loaded = load_production_configuration(repository)
    readiness = assess_implementation_readiness(loaded, repository)
    layout = build_artifact_layout(loaded, repository)
    primary_raw = configured_raw_directory(loaded, DatasetName.CORRECTED_OPTC, repository)
    secondary_raw = configured_raw_directory(
        loaded, DatasetName.TRANSPARENT_COMPUTING_ENGAGEMENT_5, repository
    )
    primary_files = discover_raw_paths(primary_raw)
    secondary_files = discover_raw_paths(secondary_raw)
    missing_directories = [path for path in layout.required_directories() if not path.exists()]
    emit(f"repository={repository}")
    emit(f"configuration={loaded.source_path}")
    emit(f"material_digest={readiness.material_digest}")
    emit(f"production_configuration_valid={readiness.production_configuration_valid}")
    emit("raw_inventory_executable=True")
    emit(f"unspecified_scientific_choice_count={readiness.unspecified_scientific_choice_count}")
    emit(f"primary_raw_directory={primary_raw}")
    emit(f"primary_raw_file_count={len(primary_files)}")
    emit(f"secondary_raw_directory={secondary_raw}")
    emit(f"secondary_raw_file_count={len(secondary_files)}")
    emit(f"missing_artifact_directories={len(missing_directories)}")
    contract_count = len(module_contracts()) + 3
    tables_contract()
    figures_contract()
    reproducibility_contract()
    emit(f"module_contracts={contract_count}")
    emit("next_action=fedcampaign preprocess")
