import typer

from fedcampaign_emhi.config.loading import load_production_configuration, repository_root
from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.execution.status import project_status
from fedcampaign_emhi.experiments.definitions import resolve_experiment_name


def status_command(
    experiment_name: str | None = typer.Argument(default=None),
) -> None:
    loaded = load_production_configuration(repository_root())
    selected: ExperimentName | None = None
    if experiment_name is not None:
        selected = resolve_experiment_name(experiment_name)
    typer.echo(f"material_digest={loaded.material_digest}")
    for item in project_status(loaded):
        if selected is not None and item.experiment_name is not selected:
            continue
        typer.echo(
            f"{item.experiment_name.value}"
            f" state={item.state.value}"
            f" development_seeds={item.development_seed_count}"
            f" confirmatory_seeds={item.confirmatory_seed_count}"
        )
