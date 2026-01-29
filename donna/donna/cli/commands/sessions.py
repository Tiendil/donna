import typer

from donna.cli.application import app
from donna.cli.types import ActionRequestIdArgument, FullArtifactIdArgument, FullArtifactSectionIdArgument
from donna.cli.utils import output_cells, try_initialize_donna, cells_cli
from donna.machine import sessions

sessions_cli = typer.Typer()


@sessions_cli.callback(invoke_without_command=True)
def initialize(ctx: typer.Context) -> None:
    cmd = ctx.invoked_subcommand

    if cmd is None:
        return

    try_initialize_donna()


@sessions_cli.command()
@cells_cli
def start() -> None:
    return sessions.start()


@sessions_cli.command(name="continue")
@cells_cli
def continue_() -> None:
    return sessions.continue_()


@sessions_cli.command()
@cells_cli
def status() -> None:
    return sessions.status()


@sessions_cli.command()
@cells_cli
def details() -> None:
    return sessions.details()


@sessions_cli.command()
@cells_cli
def run(workflow_id: FullArtifactIdArgument) -> None:
    return sessions.start_workflow(workflow_id)


@sessions_cli.command()
@cells_cli
def action_request_completed(
    request_id: ActionRequestIdArgument, next_operation_id: FullArtifactSectionIdArgument
) -> None:
    return sessions.complete_action_request(request_id, next_operation_id)


@sessions_cli.command()
@cells_cli
def clear() -> None:
    return sessions.clear()


app.add_typer(sessions_cli, name="sessions", help="Manage current session")
