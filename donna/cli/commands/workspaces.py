import pathlib
from collections.abc import Iterable

import typer

from donna.cli.application import app
from donna.cli.utils import cells_cli, try_initialize_donna
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.protocol.cells import Cell
from donna.workspaces.initialization import initialize_workspace

workspaces_cli = typer.Typer()


@workspaces_cli.callback(invoke_without_command=True)
def initialize_callback(ctx: typer.Context) -> None:
    cmd = ctx.invoked_subcommand

    if cmd is None:
        return

    if cmd in {"init"}:
        return

    try_initialize_donna()


@workspaces_cli.command(help="Initialize Donna workspace.")
@cells_cli
def init() -> Iterable[Cell]:
    initialize_workspace(pathlib.Path.cwd()).unwrap()

    return [operation_succeeded("Workspace initialized successfully")]


app.add_typer(
    workspaces_cli,
    name="workspaces",
    help="Initialize and manage Donna workspace.",
)
