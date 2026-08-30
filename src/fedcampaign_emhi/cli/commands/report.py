import typer

from fedcampaign_emhi.config.loading import production_configuration_context
from fedcampaign_emhi.domain.enums import ExperimentName, OverwritePolicy
from fedcampaign_emhi.domain.types import Boolean
from fedcampaign_emhi.reporting.evidence import materialize_report_scope

_OPTIONAL_EXPERIMENT_ARGUMENT: ExperimentName | None = typer.Argument(default=None)
_OVERWRITE_OPTION: Boolean = typer.Option(False, "--overwrite")


def report_command(
    experiment_name: ExperimentName | None = _OPTIONAL_EXPERIMENT_ARGUMENT,
    overwrite: Boolean = _OVERWRITE_OPTION,
) -> None:
    repository, loaded = production_configuration_context()
    policy = OverwritePolicy.OVERWRITE if overwrite else OverwritePolicy.REUSE_COMPATIBLE
    reports = materialize_report_scope(loaded, repository, experiment_name, policy)
    if experiment_name is not None:
        typer.echo(f"experiment={experiment_name.value}")
    else:
        typer.echo("scope=project_summary")
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"overwrite={overwrite}")
    typer.echo(f"reported_experiments={len(reports)}")
    for report in reports:
        for path in report.output_paths:
            typer.echo(f"report_artifact={path}")
