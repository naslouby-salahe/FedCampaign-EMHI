import typer

from fedcampaign_emhi.config.loading import load_smoke_configuration, repository_root
from fedcampaign_emhi.domain.enums import ExperimentName
from fedcampaign_emhi.evaluation.metrics import smoke_module_fixtures
from fedcampaign_emhi.execution.planning import RESUME_SEQUENCE


def smoke_command(
    overwrite: bool = typer.Option(False, "--overwrite"),
) -> None:
    loaded = load_smoke_configuration(repository_root())
    fixtures = smoke_module_fixtures(loaded)
    typer.echo(f"experiment={ExperimentName.SYNTHETIC_MODULE_VALIDATION.value}")
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"overwrite={overwrite}")
    typer.echo(f"blocked_fold_sizes={list(fixtures.blocked_fold_sizes)}")
    typer.echo(f"strict_odi_fixture={fixtures.strict_odi_indicator}")
    typer.echo("resume_sequence=" + " -> ".join(RESUME_SEQUENCE))
    typer.echo("must_not_invalidate=real-data scientific artifacts")
