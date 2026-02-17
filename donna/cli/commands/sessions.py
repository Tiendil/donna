from collections.abc import Iterable

import typer

from donna.cli.application import app
from donna.cli.types import ActionRequestIdArgument, FullArtifactIdArgument, FullArtifactSectionIdArgument
from donna.cli.utils import cells_cli
from donna.machine import sessions
from donna.protocol.cells import Cell

sessions_cli = typer.Typer()


@sessions_cli.command(help="Start a new session, reset session state, remove all session artifacts.")
@cells_cli
def start() -> Iterable[Cell]:
    return sessions.start().unwrap()


@sessions_cli.command(help="Reset the current session state, keeps session artifacts.")
@cells_cli
def reset() -> Iterable[Cell]:
    return sessions.reset().unwrap()


@sessions_cli.command(
    name="continue",
    help="Continue the current session and emit the next queued action request(s).",
)
@cells_cli
def continue_() -> Iterable[Cell]:
    return sessions.continue_().unwrap()


@sessions_cli.command(help="Show a concise status summary for the current session, including pending action requests.")
@cells_cli
def status() -> Iterable[Cell]:
    return sessions.status().unwrap()


@sessions_cli.command(help="Show detailed session state, including action requests.")
@cells_cli
def details() -> Iterable[Cell]:
    return sessions.details().unwrap()


@sessions_cli.command(help="Run a workflow from an artifact to drive the current session forward.")
@cells_cli
def run(workflow_id: FullArtifactIdArgument) -> Iterable[Cell]:
    return sessions.start_workflow(workflow_id).unwrap()


@sessions_cli.command(
    help="Mark an action request as completed and advance the workflow to the specified next operation."
)
@cells_cli
def action_request_completed(
    request_id: ActionRequestIdArgument, next_operation_id: FullArtifactSectionIdArgument
) -> Iterable[Cell]:
    return sessions.complete_action_request(request_id, next_operation_id).unwrap()


app.add_typer(
    sessions_cli,
    name="sessions",
    help="Manage Donna session lifecycle.",
)
