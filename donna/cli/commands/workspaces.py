from collections.abc import Iterable

import typer
import pathlib

from donna.cli.application import app
from donna.cli.utils import cells_cli
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.protocol.cells import Cell
from donna.workspaces import config as workspace_config
from donna.workspaces.initialization import initialize_workspace
from donna.workspaces import errors as workspace_errors

workspaces_cli = typer.Typer()


@workspaces_cli.command(help="Initialize Donna workspace.")
@cells_cli
def init() -> Iterable[Cell]:
    if workspace_config.project_dir.is_set():
        target_dir = workspace_config.project_dir()
    else:
        target_dir = pathlib.Path.cwd()

    initialize_workspace(target_dir).unwrap()

    return [operation_succeeded("Workspace initialized successfully")]


app.add_typer(
    workspaces_cli,
    name="workspaces",
    help="Initialize and manage Donna workspace.",
)
