import typer

from fedcampaign_emhi.config.loading import load_production_configuration, repository_root
from fedcampaign_emhi.datasets.inventory import (
    configured_raw_directory,
    discover_raw_paths,
    inventory_raw_directory,
)
from fedcampaign_emhi.domain.enums import DatasetName


def preprocess_command(
    dataset_name: str | None = typer.Argument(default=None),
    overwrite: bool = typer.Option(False, "--overwrite"),
) -> None:
    loaded = load_production_configuration(repository_root())
    repository = repository_root()
    requested: tuple[DatasetName, ...]
    if dataset_name is None:
        requested = (
            DatasetName.TON_IOT_NETWORK,
            DatasetName.EDGE_IIOTSET,
        )
    else:
        requested = (_parse_dataset_name(dataset_name),)
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"overwrite={overwrite}")
    for name in requested:
        raw_directory = configured_raw_directory(loaded, name, repository)
        files = discover_raw_paths(raw_directory)
        typer.echo(
            f"dataset={name.value} raw_directory={raw_directory} raw_file_count={len(files)}"
        )
        if files:
            typer.echo(
                f"inventory_entries={len(inventory_raw_directory(raw_directory, repository))}"
            )
    typer.echo("ownership=inventory,prepared,splits,partitions,campaign_registry")
    typer.echo("must_not_regenerate=detectors,scores,evaluations,statistics,reports")


def _parse_dataset_name(dataset_argument: str) -> DatasetName:
    aliases = {
        "ton-iot-network": DatasetName.TON_IOT_NETWORK,
        "ton_iot network": DatasetName.TON_IOT_NETWORK,
        DatasetName.TON_IOT_NETWORK.value.lower(): DatasetName.TON_IOT_NETWORK,
        "edge-iiotset": DatasetName.EDGE_IIOTSET,
        DatasetName.EDGE_IIOTSET.value.lower(): DatasetName.EDGE_IIOTSET,
    }
    resolved = aliases.get(dataset_argument.lower())
    if resolved is None:
        raise typer.BadParameter(f"unknown dataset name {dataset_argument}")
    return resolved
