import typer

from fedcampaign_emhi.config.loading import production_configuration_context
from fedcampaign_emhi.domain.enums import ExperimentName, ExperimentState, OverwritePolicy
from fedcampaign_emhi.domain.types import Boolean
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE, resolve_requested_experiment
from fedcampaign_emhi.execution.runner import execute_experiment
from fedcampaign_emhi.experiments.validation import assert_known_experiment

_REQUESTED_EXPERIMENT_ARGUMENT: ExperimentName = typer.Argument()
_OVERWRITE_OPTION: Boolean = typer.Option(False, "--overwrite")
_DRY_RUN_OPTION: Boolean = typer.Option(False, "--dry-run")


def run_command(
    requested: ExperimentName = _REQUESTED_EXPERIMENT_ARGUMENT,
    overwrite: Boolean = _OVERWRITE_OPTION,
    dry_run: Boolean = _DRY_RUN_OPTION,
) -> None:
    repository, loaded = production_configuration_context()
    resolved = resolve_requested_experiment(requested.value)
    assert_known_experiment(loaded.values, resolved)
    if dry_run:
        typer.echo(f"experiment={resolved.value}")
        typer.echo(f"material_digest={loaded.material_digest}")
        typer.echo("scientific_configuration_overrides=rejected")
        typer.echo("dry_run=true")
        typer.echo("resume_sequence=" + " -> ".join(RESUME_SEQUENCE))
        return
    policy = OverwritePolicy.OVERWRITE if overwrite else OverwritePolicy.REUSE_COMPATIBLE
    result = execute_experiment(loaded, repository, resolved, policy)
    typer.echo(f"experiment={resolved.value}")
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"overwrite={overwrite}")
    typer.echo("scientific_configuration_overrides=rejected")
    typer.echo(f"run_record={result.run_record_path}")
    typer.echo(f"state={result.state.value}")
    typer.echo(f"completed_cells={result.completed_cell_count}")
    typer.echo(f"detail={result.detail}")
    typer.echo("resume_sequence=" + " -> ".join(RESUME_SEQUENCE))
    if result.state in {ExperimentState.FAILED, ExperimentState.INVALID}:
        raise typer.Exit(code=1)
