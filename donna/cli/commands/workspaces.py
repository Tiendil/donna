from collections.abc import Iterable

import typer

from donna.cli.application import app
from donna.cli.utils import cells_cli
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.protocol.cells import Cell
from donna.workspaces import config as workspace_config
from donna.workspaces.initialization import initialize_workspace

workspaces_cli = typer.Typer()


@workspaces_cli.command(help="Initialize Donna workspace.")
@cells_cli
def init() -> Iterable[Cell]:
    target_dir = workspace_config.project_dir()
    initialize_workspace(target_dir).unwrap()

    return [operation_succeeded("Workspace initialized successfully")]


app.add_typer(
    workspaces_cli,
    name="workspaces",
    help="Initialize and manage Donna workspace.",
)
