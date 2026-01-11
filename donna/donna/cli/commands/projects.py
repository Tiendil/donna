import pathlib

import typer

from donna.cli.application import app
from donna.world.config import config

projects_cli = typer.Typer()


@projects_cli.command()
def initialize(workdir: pathlib.Path = pathlib.Path.cwd()) -> None:
    config().get_world("project").initialize()
    config().get_world("session").initialize()


app.add_typer(projects_cli, name="projects", help="Manage projects")
