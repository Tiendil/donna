import pathlib
from collections.abc import Iterable

import typer

from donna.cli.application import app
from donna.cli.types import SkillsOption
from donna.cli.utils import cells_cli
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.protocol.cells import Cell
from donna.workspaces import config as workspace_config
from donna.workspaces.initialization import initialize_workspace, update_workspace

workspaces_cli = typer.Typer()


def _resolve_target_dir() -> pathlib.Path:
    if workspace_config.project_dir.is_set():
        return workspace_config.project_dir()

    return pathlib.Path.cwd()


@workspaces_cli.command(help="Initialize Donna workspace.")
@cells_cli
def init(skills: SkillsOption = True) -> Iterable[Cell]:
    target_dir = _resolve_target_dir()

    initialize_workspace(target_dir, install_skills=skills).unwrap()

    return [operation_succeeded("Workspace initialized successfully")]


@workspaces_cli.command(help="Update Donna workspace files.")
@cells_cli
def update(skills: SkillsOption = True) -> Iterable[Cell]:
    target_dir = _resolve_target_dir()

    update_workspace(target_dir, install_skills=skills).unwrap()

    return [operation_succeeded("Workspace updated successfully")]


app.add_typer(
    workspaces_cli,
    name="workspaces",
    help="Initialize and manage Donna workspace.",
)
