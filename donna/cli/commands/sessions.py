import typer

from donna.cli.application import app
from donna.cli.types import (
    ActionRequestIdArgument,
    ArtifactIdArgument,
    ArtifactSectionIdArgument,
    parse_artifact_id_argument,
    parse_artifact_section_id_argument,
)
from donna.cli.utils import command_context
from donna.machine import sessions


@app.command(help="Start a new session, reset session state, remove all session artifacts.")
def start(context: typer.Context) -> None:
    with command_context(context) as command:
        command.write_cells(sessions.start().unwrap())


@app.command(help="Reset the current session state, keeps session artifacts.")
def reset(context: typer.Context) -> None:
    with command_context(context) as command:
        command.write_cells(sessions.reset().unwrap())


@app.command(
    name="continue",
    help="Continue the current session and emit the next queued action request(s).",
)
def continue_(context: typer.Context) -> None:
    with command_context(context) as command:
        command.write_cells(sessions.continue_().unwrap())


@app.command(help="Show a concise status summary for the current session, including pending action requests.")
def status(context: typer.Context) -> None:
    with command_context(context) as command:
        command.write_cells(sessions.status().unwrap())


@app.command(help="Show detailed session state, including action requests.")
def details(context: typer.Context) -> None:
    with command_context(context) as command:
        command.write_cells(sessions.details().unwrap())


@app.command(help="Run a workflow from an artifact to drive the current session forward.")
def run(context: typer.Context, workflow_path: ArtifactIdArgument) -> None:
    with command_context(context) as command:
        workflow_id = parse_artifact_id_argument(workflow_path, command.target_dir())
        command.write_cells(sessions.start_workflow(workflow_id).unwrap())


@app.command(
    name="complete-action-request",
    help="Mark an action request as completed and advance the workflow to the specified next operation.",
)
def complete_action_request(
    context: typer.Context,
    request_id: ActionRequestIdArgument,
    next_operation_path: ArtifactSectionIdArgument,
) -> None:
    with command_context(context) as command:
        next_operation_id = parse_artifact_section_id_argument(next_operation_path, command.target_dir())
        command.write_cells(sessions.complete_action_request(request_id, next_operation_id).unwrap())
