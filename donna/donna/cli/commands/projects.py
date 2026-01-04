import pathlib

import typer

from donna.cli.application import app
from donna.world.layout import layout

projects_cli = typer.Typer()


@projects_cli.command()
def initialize(workdir: pathlib.Path = pathlib.Path.cwd()) -> None:
    # all initialization logic is in constructor
    layout(workdir, create_donna_dir=True)


app.add_typer(projects_cli, name="projects", help="Manage projects")
