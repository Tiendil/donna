import typer

from donna.cli.types import ProtocolModeOption, RootOption
from donna.cli.utils import try_initialize_donna

app = typer.Typer(help="Donna CLI: manage hierarchical state machines to guide your AI agents.")


@app.callback()
def initialize(
    protocol: ProtocolModeOption = None,
    root_dir: RootOption = None,
) -> None:
    if protocol is None:
        typer.echo("Error: protocol is required. Examples: --protocol=llm or -p llm.", err=True)
        raise typer.Exit(code=2)

    try_initialize_donna(project_dir=root_dir, protocol=protocol)
