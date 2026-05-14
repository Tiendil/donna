import typer

from donna.cli.application import app
from donna.cli.types import (
    ActionRequestIdArgument,
    ArtifactIdArgument,
    ArtifactSectionIdArgument,
)
from donna.cli.utils import command_context
from donna.machine import sessions

sessions_cli = typer.Typer()


@sessions_cli.command(help="Start a new session, reset session state, remove all session artifacts.")
def start(context: typer.Context) -> None:
    with command_context(context) as command:
        command.write_cells(sessions.start().unwrap())


@sessions_cli.command(help="Reset the current session state, keeps session artifacts.")
def reset(context: typer.Context) -> None:
    with command_context(context) as command:
        command.write_cells(sessions.reset().unwrap())


@sessions_cli.command(
    name="continue",
    help="Continue the current session and emit the next queued action request(s).",
)
def continue_(context: typer.Context) -> None:
    with command_context(context) as command:
        command.write_cells(sessions.continue_().unwrap())


@sessions_cli.command(help="Show a concise status summary for the current session, including pending action requests.")
def status(context: typer.Context) -> None:
    with command_context(context) as command:
        command.write_cells(sessions.status().unwrap())


@sessions_cli.command(help="Show detailed session state, including action requests.")
def details(context: typer.Context) -> None:
    with command_context(context) as command:
        command.write_cells(sessions.details().unwrap())


@sessions_cli.command(help="Run a workflow from an artifact to drive the current session forward.")
def run(context: typer.Context, workflow_id: ArtifactIdArgument) -> None:
    with command_context(context) as command:
        command.write_cells(sessions.start_workflow(workflow_id).unwrap())


@sessions_cli.command(
    help="Mark an action request as completed and advance the workflow to the specified next operation."
)
def action_request_completed(
    context: typer.Context,
    request_id: ActionRequestIdArgument,
    next_operation_id: ArtifactSectionIdArgument,
) -> None:
    with command_context(context) as command:
        command.write_cells(sessions.complete_action_request(request_id, next_operation_id).unwrap())


app.add_typer(
    sessions_cli,
    name="sessions",
    help="Manage Donna session lifecycle.",
)
