import typer

from donna.cli.types import ProtocolModeOption
from donna.protocol.modes import set_mode

app = typer.Typer(help="Donna CLI: manage hierarchical state machines to guide your AI agents.")


@app.callback()
def initialize(
    protocol: ProtocolModeOption = None,
) -> None:
    if protocol is None:
        typer.echo("Error: protocol is required. Examples: --protocol=llm or -p llm.", err=True)
        raise typer.Exit(code=2)

    set_mode(protocol)
