import typer

from fedcampaign_emhi.config.loading import load_production_configuration, repository_root
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE, resolve_requested_experiment
from fedcampaign_emhi.experiments.validation import assert_known_experiment


def run_command(
    experiment_name: str = typer.Argument(),
    overwrite: bool = typer.Option(False, "--overwrite"),
) -> None:
    loaded = load_production_configuration(repository_root())
    resolved = resolve_requested_experiment(experiment_name)
    assert_known_experiment(loaded.values, resolved)
    typer.echo(f"experiment={resolved.value}")
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"overwrite={overwrite}")
    typer.echo("resume_sequence=" + " -> ".join(RESUME_SEQUENCE))
    typer.echo("shared_artifacts_reused_when_fingerprints_match=true")
    typer.echo("scientific_configuration_overrides=rejected")
