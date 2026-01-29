import typer

from donna.protocol.modes import Mode, set_mode
from donna.world.templates import RenderMode, set_default_render_mode

app = typer.Typer()


@app.callback()
def initialize(
    protocol: Mode | None = typer.Option(
        None,
        "--protocol",
        "-p",
        help="Protocol mode to use (required). Examples: --protocol=llm, -p llm.",
    )
) -> None:
    if protocol is None:
        typer.echo("Error: protocol is required. Examples: --protocol=llm or -p llm.", err=True)
        raise typer.Exit(code=2)

    set_mode(protocol)
    set_default_render_mode(RenderMode.cli)
