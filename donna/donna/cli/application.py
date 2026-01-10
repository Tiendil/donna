import typer

from donna.world.primitives_register import register
from donna.world.templates import RenderMode, set_default_render_mode

app = typer.Typer()


@app.callback()
def initialize() -> None:
    set_default_render_mode(RenderMode.cli)
    register()
