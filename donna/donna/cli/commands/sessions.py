import typer

from donna.cli.application import app
from donna.cli.types import ActionRequestIdArgument, FullArtifactIdArgument, FullArtifactSectionIdArgument
from donna.cli.utils import output_cells
from donna.machine import sessions

sessions_cli = typer.Typer()


@sessions_cli.command()
def start() -> None:
    output_cells(sessions.start())


@sessions_cli.command(name="continue")
def continue_() -> None:
    output_cells(sessions.continue_())


@sessions_cli.command()
def status() -> None:
    output_cells(sessions.status())


@sessions_cli.command()
def run(workflow_id: FullArtifactIdArgument) -> None:
    output_cells(sessions.start_workflow(workflow_id))


@sessions_cli.command()
def action_request_completed(
    request_id: ActionRequestIdArgument, next_operation_id: FullArtifactSectionIdArgument
) -> None:
    output_cells(sessions.complete_action_request(request_id, next_operation_id))


@sessions_cli.command()
def clear() -> None:
    output_cells(sessions.clear())


app.add_typer(sessions_cli, name="sessions", help="Manage current session")
