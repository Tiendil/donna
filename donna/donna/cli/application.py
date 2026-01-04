import typer

from donna.world.primitives_register import register

app = typer.Typer()


@app.callback()
def initialize() -> None:
    register()
