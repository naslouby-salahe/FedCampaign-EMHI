import typer

from fedcampaign_emhi.analysis.project import materialize_primary_holm_family
from fedcampaign_emhi.config.loading import production_configuration_context


def analyze_command() -> None:
    repository, loaded = production_configuration_context()
    primary_holm_path = materialize_primary_holm_family(loaded, repository)
    typer.echo(f"material_digest={loaded.material_digest}")
    typer.echo(f"primary_holm_artifact={primary_holm_path}")
