from typer.testing import CliRunner

from fedcampaign_emhi.cli import application


def test_doctor_plan_and_smoke(cli_runner: CliRunner) -> None:
    doctor = cli_runner.invoke(application, ["doctor"])
    assert doctor.exit_code == 0
    assert "production_configuration_valid=True" in doctor.stdout
    plan = cli_runner.invoke(application, ["plan"])
    assert plan.exit_code == 0
    smoke = cli_runner.invoke(application, ["smoke"])
    assert smoke.exit_code == 0
    assert "smoke_validation=PASS" in smoke.stdout
