from typer.testing import CliRunner

from fedcampaign_emhi.cli.main import application

runner = CliRunner()


def test_status_and_report() -> None:
    status = runner.invoke(application, ["status"])
    assert status.exit_code == 0
    report = runner.invoke(application, ["report"])
    assert report.exit_code == 0
    assert "results_are_scientific_inputs=False" in report.stdout
