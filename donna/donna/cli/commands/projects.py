import pathlib

import typer

from donna.cli.application import app
from donna.cli.utils import try_initialize_donna
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
def initialize(workdir: pathlib.Path = pathlib.Path.cwd()) -> None:
    config().get_world(WorldId("project")).initialize()
    config().get_world(WorldId("session")).initialize()


app.add_typer(projects_cli, name="projects", help="Manage projects")
