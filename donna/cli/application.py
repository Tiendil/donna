import typer

from donna.cli.types import ProtocolModeOption, RootOption
from donna.protocol.modes import set_mode

app = typer.Typer(help="Donna CLI: manage hierarchical state machines to guide your AI agents.")


@app.callback()
def initialize(
    ctx: typer.Context,
    protocol: ProtocolModeOption = None,
    root_dir: RootOption = None,
) -> None:
    if protocol is None:
        typer.echo("Error: protocol is required. Examples: --protocol=llm or -p llm.", err=True)
        raise typer.Exit(code=2)

    set_mode(protocol)

    if ctx.obj is None:
        ctx.obj = {}

    ctx.obj["root_dir"] = root_dir
