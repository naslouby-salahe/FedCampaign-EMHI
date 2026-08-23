import typer

from fedcampaign_emhi.config.loading import production_configuration_context
from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.execution.status import project_status

_OPTIONAL_EXPERIMENT_ARGUMENT: ExperimentName | None = typer.Argument(default=None)


def status_command(
    experiment_name: ExperimentName | None = _OPTIONAL_EXPERIMENT_ARGUMENT,
) -> None:
    _, loaded = production_configuration_context()
    typer.echo(f"material_digest={loaded.material_digest}")
    for item in project_status(loaded):
        if experiment_name is not None and item.experiment_name is not experiment_name:
            continue
        typer.echo(
            f"{item.experiment_name.value}"
            f" state={item.state.value}"
            f" development_seeds={item.development_seed_count}"
            f" confirmatory_seeds={item.confirmatory_seed_count}"
        )
