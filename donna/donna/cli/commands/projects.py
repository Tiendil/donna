import pathlib

import typer

from donna.cli.application import app
from donna.cli.utils import output_cells, try_initialize_donna, cells_cli
from donna.domain.ids import WorldId
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


@projects_cli.command()
@cells_cli
def initialize(workdir: pathlib.Path = pathlib.Path.cwd()) -> None:
    project_result = config().get_world(WorldId("project"))
    if project_result.is_err():
        return [error.node().info() for error in project_result.unwrap_err()]

    project_result.unwrap().initialize()

    session_result = config().get_world(WorldId("session"))
    if session_result.is_err():
        return [error.node().info() for error in session_result.unwrap_err()]

    session_result.unwrap().initialize()

    return [operation_succeeded("Project initialized successfully")]


app.add_typer(projects_cli, name="projects", help="Manage projects")
