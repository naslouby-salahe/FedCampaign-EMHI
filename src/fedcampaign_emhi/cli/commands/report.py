import typer

from fedcampaign_emhi.config.loading import load_production_configuration, repository_root
from fedcampaign_emhi.experiments.definitions import resolve_experiment_name
from fedcampaign_emhi.reporting.evidence import (
    results_are_scientific_inputs,
    results_are_terminal_exports,
)


def report_command(
    experiment_name: str | None = typer.Argument(default=None),
    overwrite: bool = typer.Option(False, "--overwrite"),
) -> None:
    loaded = load_production_configuration(repository_root())
    if experiment_name is not None:
        resolved = resolve_experiment_name(experiment_name)
        typer.echo(f"experiment={resolved.value}")
    else:
        typer.echo("scope=project_summary")
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"overwrite={overwrite}")
    typer.echo(f"results_are_terminal_exports={results_are_terminal_exports()}")
    typer.echo(f"results_are_scientific_inputs={results_are_scientific_inputs()}")
    typer.echo(
        "must_not_regenerate=preprocessing,fitting,scoring,calibration,evaluation,statistics"
    )
