import typer

from donna.world import register

app = typer.Typer()


@app.callback()
def initialize():
    register()
