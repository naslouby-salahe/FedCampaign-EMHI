import typer

from fedcampaign_emhi.config.loading import production_configuration_context
from fedcampaign_emhi.domain.enums import DatasetName, OverwritePolicy, PreprocessingLayer
from fedcampaign_emhi.execution.preprocess import (
    execute_preprocess,
    preprocess_must_not_regenerate,
    requested_datasets,
)


def preprocess_command(
    dataset_name: str | None = typer.Argument(default=None),
    overwrite: bool = typer.Option(False, "--overwrite"),
) -> None:
    repository, loaded = production_configuration_context()
    selected = None if dataset_name is None else _parse_dataset_name(dataset_name)
    policy = OverwritePolicy.OVERWRITE if overwrite else OverwritePolicy.REUSE_COMPATIBLE
    record = execute_preprocess(loaded, repository, selected, policy)
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"overwrite={overwrite}")
    typer.echo("datasets=" + ",".join(name.value for name in requested_datasets(selected)))
    for dataset, start_layer in record.reconstruct_from:
        origin = start_layer.value if start_layer is not None else "reuse_all"
        typer.echo(f"reconstruct_from.{dataset.value}={origin}")
    reused = tuple(decision.layer.value for decision in record.decisions if decision.reused)
    rebuilt = tuple(decision.layer.value for decision in record.decisions if decision.reconstructed)
    typer.echo("reused_layers=" + ",".join(reused))
    typer.echo("rebuilt_layers=" + ",".join(rebuilt))
    invalidated = tuple(
        artifact_id
        for decision in record.decisions
        for artifact_id in decision.invalidated_descendant_ids
    )
    typer.echo("invalidated_descendants=" + ",".join(invalidated))
    typer.echo("ownership=" + ",".join(layer.value for layer in PreprocessingLayer))
    typer.echo(
        "must_not_regenerate=" + ",".join(kind.value for kind in preprocess_must_not_regenerate())
    )


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
