import pathlib

import typer

from donna.cli.application import app
from donna.domain.ids import WorldId
from donna.world.config import config
from donna.cli.utils import try_initialize_donna

projects_cli = typer.Typer()


@projects_cli.callback(invoke_without_command=True)
def initialize(ctx: typer.Context):
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
