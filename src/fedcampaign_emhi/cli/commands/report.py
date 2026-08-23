import typer

from fedcampaign_emhi.config.loading import production_configuration_context
from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.reporting.evidence import (
    results_are_scientific_inputs,
    results_are_terminal_exports,
)

_OPTIONAL_EXPERIMENT_ARGUMENT: ExperimentName | None = typer.Argument(default=None)


def report_command(
    experiment_name: ExperimentName | None = _OPTIONAL_EXPERIMENT_ARGUMENT,
    overwrite: bool = typer.Option(False, "--overwrite"),
) -> None:
    _, loaded = production_configuration_context()
    if experiment_name is not None:
        typer.echo(f"experiment={experiment_name.value}")
    else:
        typer.echo("scope=project_summary")
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"overwrite={overwrite}")
    typer.echo(f"results_are_terminal_exports={results_are_terminal_exports()}")
    typer.echo(f"results_are_scientific_inputs={results_are_scientific_inputs()}")
    typer.echo(
        "must_not_regenerate=preprocessing,fitting,scoring,calibration,evaluation,statistics"
    )
