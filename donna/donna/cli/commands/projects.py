import pathlib
from collections.abc import Iterable

import typer

from donna.cli.application import app
from donna.cli.types import WorkdirOption
from donna.cli.utils import cells_cli, try_initialize_donna
from donna.domain.ids import WorldId
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.protocol.cells import Cell
from donna.world.config import config

projects_cli = typer.Typer()


@projects_cli.callback(invoke_without_command=True)
def initialize_callback(ctx: typer.Context) -> None:
    cmd = ctx.invoked_subcommand

    if cmd is None:
        return

    if cmd in ["initialize"]:
        return

    try_initialize_donna()


@projects_cli.command(
    help="Initialize Donna project."
)
@cells_cli
def initialize(workdir: WorkdirOption = pathlib.Path.cwd()) -> Iterable[Cell]:
    # TODO: use workdir attribute
    project = config().get_world(WorldId("project")).unwrap()

    project.initialize()

    session = config().get_world(WorldId("session")).unwrap()

    session.initialize()

    return [operation_succeeded("Project initialized successfully")]


app.add_typer(
    projects_cli,
    name="projects",
    help="Initialize and manage Donna project.",
)
