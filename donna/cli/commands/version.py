import importlib.metadata

import typer

from donna.cli.application import app


@app.command(help="Print the current Donna package version.")
def version() -> None:
    typer.echo(importlib.metadata.version("donna"))
