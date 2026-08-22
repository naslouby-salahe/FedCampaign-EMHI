from typer.testing import CliRunner

from fedcampaign_emhi.cli.main import application

runner = CliRunner()


def test_doctor_plan_and_smoke() -> None:
    doctor = runner.invoke(application, ["doctor"])
    assert doctor.exit_code == 0
    assert "production_configuration_valid=True" in doctor.stdout
    plan = runner.invoke(application, ["plan"])
    assert plan.exit_code == 0
    smoke = runner.invoke(application, ["smoke"])
    assert smoke.exit_code == 0
    assert "smoke_gate=PASS" in smoke.stdout
