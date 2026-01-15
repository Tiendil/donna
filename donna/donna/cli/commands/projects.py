import pathlib

import typer

from donna.cli.application import app
from donna.domain.ids import WorldId
from donna.world.config import config

projects_cli = typer.Typer()


@projects_cli.command()
def initialize(workdir: pathlib.Path = pathlib.Path.cwd()) -> None:
    config().get_world(WorldId("project")).initialize()
    config().get_world(WorldId("session")).initialize()


app.add_typer(projects_cli, name="projects", help="Manage projects")
