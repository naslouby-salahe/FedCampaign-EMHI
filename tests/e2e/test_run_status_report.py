from typer.testing import CliRunner

from fedcampaign_emhi.cli import application


def test_status_and_report_rejects_unverified_evidence(cli_runner: CliRunner) -> None:
    status = cli_runner.invoke(application, ["status"])
    assert status.exit_code == 0
    report = cli_runner.invoke(application, ["report", "pure-order-separation-validation"])
    assert report.exit_code == 1
    assert report.exception is not None
    assert any(
        marker in str(report.exception)
        for marker in ("missing run record", "stale for the active configuration")
    )


def test_project_summary_rejects_unverified_primary_holm_evidence(cli_runner: CliRunner) -> None:
    report = cli_runner.invoke(application, ["report"])

    assert report.exit_code == 1
    assert report.exception is not None
    assert any(
        marker in str(report.exception)
        for marker in ("missing run record", "stale for the active configuration")
    )
