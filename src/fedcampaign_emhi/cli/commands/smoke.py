import typer

from fedcampaign_emhi.config.loading import load_smoke_configuration, repository_root
from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.evaluation.smoke_gate import run_synthetic_module_validation
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE


def smoke_command(
    overwrite: bool = typer.Option(False, "--overwrite"),
) -> None:
    loaded = load_smoke_configuration(repository_root())
    gate = run_synthetic_module_validation(loaded)
    typer.echo(f"experiment={ExperimentName.SYNTHETIC_MODULE_VALIDATION.value}")
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"overwrite={overwrite}")
    typer.echo(f"smoke_gate={'PASS' if gate.passed else 'FAIL'}")
    for failure in gate.failures:
        typer.echo(f"smoke_failure={failure}")
    typer.echo("resume_sequence=" + " -> ".join(RESUME_SEQUENCE))
    typer.echo("must_not_invalidate=real-data scientific artifacts")
    raise typer.Exit(code=0 if gate.passed else 1)
