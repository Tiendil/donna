import typer

from donna.world.primitives_register import register
from donna.world.templates import set_default_render_mode, RenderMode

app = typer.Typer()


@app.callback()
def initialize() -> None:
    set_default_render_mode(RenderMode.cli)
    register()
