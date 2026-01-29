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


@sessions_cli.command()
@cells_cli
def start() -> Iterable[Cell]:
    return sessions.start()


@sessions_cli.command(name="continue")
@cells_cli
def continue_() -> Iterable[Cell]:
    return sessions.continue_()


@sessions_cli.command()
@cells_cli
def status() -> Iterable[Cell]:
    return sessions.status()


@sessions_cli.command()
@cells_cli
def details() -> Iterable[Cell]:
    return sessions.details()


@sessions_cli.command()
@cells_cli
def run(workflow_id: FullArtifactIdArgument) -> Iterable[Cell]:
    return sessions.start_workflow(workflow_id)


@sessions_cli.command()
@cells_cli
def action_request_completed(
    request_id: ActionRequestIdArgument, next_operation_id: FullArtifactSectionIdArgument
) -> Iterable[Cell]:
    return sessions.complete_action_request(request_id, next_operation_id)


@sessions_cli.command()
@cells_cli
def clear() -> Iterable[Cell]:
    return sessions.clear()


app.add_typer(sessions_cli, name="sessions", help="Manage current session")
