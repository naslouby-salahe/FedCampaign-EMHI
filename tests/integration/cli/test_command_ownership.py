import pytest
from typer.testing import CliRunner

from fedcampaign_emhi.cli.main import application
from fedcampaign_emhi.domain.enums import ExperimentName


def test_public_commands_exist(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(application, ["--help"])
    assert result.exit_code == 0
    for command in (
        "doctor",
        "preprocess",
        "plan",
        "smoke",
        "run",
        "status",
        "analyze",
        "report",
    ):
        assert command in result.stdout


def test_run_rejects_unknown_experiment(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(application, ["run", "not-an-experiment"])
    assert result.exit_code != 0


def test_run_accepts_roadmap_experiment(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(
        application,
        ["run", ExperimentName.PRIMARY_STRICT_ODI_EVALUATION.value, "--dry-run"],
    )
    assert result.exit_code == 0
    assert "scientific_configuration_overrides=rejected" in result.stdout
    assert "dry_run=true" in result.stdout


def test_dry_run_never_reaches_experiment_execution(
    cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject_execution(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("dry run must not execute an experiment")

    monkeypatch.setattr("fedcampaign_emhi.cli.commands.run.execute_experiment", reject_execution)

    result = cli_runner.invoke(
        application,
        ["run", ExperimentName.PRIMARY_STRICT_ODI_EVALUATION.value, "--dry-run"],
    )

    assert result.exit_code == 0


def test_no_seed_override_option(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(application, ["run", "--help"])
    assert "--seed" not in result.stdout
    assert "--method" not in result.stdout


def test_preprocess_help_exposes_overwrite_not_scientific_flags(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(application, ["preprocess", "--help"])
    assert result.exit_code == 0
    assert "--overwrite" in result.stdout
    assert "--seed" not in result.stdout
    assert "--method" not in result.stdout
