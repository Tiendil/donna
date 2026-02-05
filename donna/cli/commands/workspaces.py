import pathlib
from collections.abc import Iterable

import typer

from donna.cli.application import app
from donna.cli.types import ProjectDirArgument
from donna.cli.utils import cells_cli, root_dir_from_context, try_initialize_donna
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
def init(project_dir: ProjectDirArgument = None) -> Iterable[Cell]:
    target_dir = project_dir or root_dir_from_context() or pathlib.Path.cwd()
    initialize_workspace(target_dir).unwrap()

    return [operation_succeeded("Workspace initialized successfully")]


app.add_typer(
    workspaces_cli,
    name="workspaces",
    help="Initialize and manage Donna workspace.",
)
