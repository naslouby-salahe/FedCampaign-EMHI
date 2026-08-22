from typer.testing import CliRunner

from fedcampaign_emhi.cli.main import application
from fedcampaign_emhi.domain.enums import ExperimentName

runner = CliRunner()


def test_public_commands_exist() -> None:
    result = runner.invoke(application, ["--help"])
    assert result.exit_code == 0
    for command in ("doctor", "preprocess", "plan", "smoke", "run", "status", "report"):
        assert command in result.stdout


def test_run_rejects_unknown_experiment() -> None:
    result = runner.invoke(application, ["run", "not-an-experiment"])
    assert result.exit_code != 0


def test_run_accepts_roadmap_experiment() -> None:
    result = runner.invoke(application, ["run", ExperimentName.PRIMARY_STRICT_ODI_EVALUATION.value])
    assert result.exit_code == 0
    assert "scientific_configuration_overrides=rejected" in result.stdout


def test_no_seed_override_option() -> None:
    result = runner.invoke(application, ["run", "--help"])
    assert "--seed" not in result.stdout
    assert "--method" not in result.stdout
