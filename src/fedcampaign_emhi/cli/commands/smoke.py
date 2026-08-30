import typer

from fedcampaign_emhi.config.loading import load_smoke_configuration, repository_root
from fedcampaign_emhi.domain.enums import ExperimentName, ExperimentState, OverwritePolicy
from fedcampaign_emhi.domain.types import Boolean
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE
from fedcampaign_emhi.execution.runner import execute_experiment

_OVERWRITE_OPTION: Boolean = typer.Option(False, "--overwrite")


def smoke_command(
    overwrite: Boolean = _OVERWRITE_OPTION,
) -> None:
    repository = repository_root()
    loaded = load_smoke_configuration(repository)
    policy = OverwritePolicy.OVERWRITE if overwrite else OverwritePolicy.REUSE_COMPATIBLE
    result = execute_experiment(
        loaded,
        repository,
        ExperimentName.SYNTHETIC_MODULE_VALIDATION,
        policy,
    )
    typer.echo(f"experiment={ExperimentName.SYNTHETIC_MODULE_VALIDATION.value}")
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"overwrite={overwrite}")
    typer.echo(f"smoke_gate={'PASS' if result.state is ExperimentState.COMPLETED else 'FAIL'}")
    typer.echo(f"state={result.state.value}")
    typer.echo(f"completed_cells={result.completed_cell_count}")
    typer.echo(f"detail={result.detail}")
    typer.echo("resume_sequence=" + " -> ".join(RESUME_SEQUENCE))
    typer.echo("must_not_invalidate=real-data scientific artifacts")
    if result.state is not ExperimentState.COMPLETED:
        raise typer.Exit(code=1)
