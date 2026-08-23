from typer.testing import CliRunner

from fedcampaign_emhi.cli.main import application


def test_status_and_report(cli_runner: CliRunner) -> None:
    status = cli_runner.invoke(application, ["status"])
    assert status.exit_code == 0
    report = cli_runner.invoke(application, ["report"])
    assert report.exit_code == 0
    assert "results_are_scientific_inputs=False" in report.stdout
