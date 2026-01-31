from collections.abc import Iterable

import typer

from donna.cli.application import app
from donna.cli.types import ActionRequestIdArgument, FullArtifactIdArgument, FullArtifactSectionIdArgument
from donna.cli.utils import cells_cli, try_initialize_donna
from donna.machine import sessions
from donna.protocol.cells import Cell

sessions_cli = typer.Typer()


@sessions_cli.callback(invoke_without_command=True)
def initialize(ctx: typer.Context) -> None:
    cmd = ctx.invoked_subcommand

    if cmd is None:
        return

    try_initialize_donna()


@sessions_cli.command(help="Start a new session, reset session state, remove all session artifacts.")
@cells_cli
def start() -> Iterable[Cell]:
    return sessions.start()


@sessions_cli.command(help="Reset the current session state, keeps session artifacts.")
@cells_cli
def reset() -> Iterable[Cell]:
    return sessions.reset()


@sessions_cli.command(
    name="continue",
    help="Continue the current session and emit the next queued action request(s).",
)
@cells_cli
def continue_() -> Iterable[Cell]:
    return sessions.continue_()


@sessions_cli.command(help="Show a concise status summary for the current session, including pending action requests.")
@cells_cli
def status() -> Iterable[Cell]:
    return sessions.status()


@sessions_cli.command(help="Show detailed session state, including action requests.")
@cells_cli
def details() -> Iterable[Cell]:
    return sessions.details()


@sessions_cli.command(help="Run a workflow fron an artifact to drive the current session forward.")
@cells_cli
def run(workflow_id: FullArtifactIdArgument) -> Iterable[Cell]:
    return sessions.start_workflow(workflow_id)


@sessions_cli.command(
    help="Mark an action request as completed and advance the workflow to the specified next operation."
)
@cells_cli
def action_request_completed(
    request_id: ActionRequestIdArgument, next_operation_id: FullArtifactSectionIdArgument
) -> Iterable[Cell]:
    return sessions.complete_action_request(request_id, next_operation_id)


app.add_typer(
    sessions_cli,
    name="sessions",
    help="Manage Donna session lifecycle.",
)
