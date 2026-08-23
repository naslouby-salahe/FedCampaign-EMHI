import typer

from fedcampaign_emhi.config.loading import load_production_configuration, repository_root
from fedcampaign_emhi.domain.enums import ExperimentName, OverwritePolicy
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE, resolve_requested_experiment
from fedcampaign_emhi.execution.runner import publish_experiment_run_record
from fedcampaign_emhi.experiments.validation import assert_known_experiment


def run_command(
    experiment_name: str = typer.Argument(),
    overwrite: bool = typer.Option(False, "--overwrite"),
) -> None:
    try:
        requested = ExperimentName(experiment_name)
    except ValueError as error:
        typer.echo(f"unknown experiment name {experiment_name}")
        raise typer.Exit(code=2) from error
    repository = repository_root()
    loaded = load_production_configuration(repository)
    resolved = resolve_requested_experiment(requested.value)
    assert_known_experiment(loaded.values, resolved)
    policy = OverwritePolicy.OVERWRITE if overwrite else OverwritePolicy.REUSE_COMPATIBLE
    record_path = publish_experiment_run_record(loaded, repository, resolved, policy)
    typer.echo(f"experiment={resolved.value}")
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"overwrite={overwrite}")
    typer.echo(f"run_record={record_path}")
    typer.echo("resume_sequence=" + " -> ".join(RESUME_SEQUENCE))
    typer.echo("shared_artifacts_reused_when_fingerprints_match=true")
    typer.echo("scientific_configuration_overrides=rejected")
