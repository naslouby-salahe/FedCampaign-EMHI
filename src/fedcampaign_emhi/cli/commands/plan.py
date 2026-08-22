import typer

from fedcampaign_emhi.config.loading import load_production_configuration, repository_root
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE, plan_experiments


def plan_command() -> None:
    loaded = load_production_configuration(repository_root())
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo("resume_sequence=" + " -> ".join(RESUME_SEQUENCE))
    for planned in plan_experiments(loaded):
        typer.echo(
            f"{planned.experiment_name.value}"
            f" role={planned.execution_role.value}"
            f" seeds={planned.seed_count}"
            f" state={planned.state.value}"
        )
