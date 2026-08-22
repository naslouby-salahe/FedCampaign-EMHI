import typer

from fedcampaign_emhi.cli.commands.doctor import doctor_command
from fedcampaign_emhi.cli.commands.plan import plan_command
from fedcampaign_emhi.cli.commands.preprocess import preprocess_command
from fedcampaign_emhi.cli.commands.report import report_command
from fedcampaign_emhi.cli.commands.run import run_command
from fedcampaign_emhi.cli.commands.smoke import smoke_command
from fedcampaign_emhi.cli.commands.status import status_command

application = typer.Typer(
    add_completion=False, no_args_is_help=True, pretty_exceptions_show_locals=False
)
application.command("doctor")(doctor_command)
application.command("preprocess")(preprocess_command)
application.command("plan")(plan_command)
application.command("smoke")(smoke_command)
application.command("run")(run_command)
application.command("status")(status_command)
application.command("report")(report_command)


def main() -> None:
    application()
