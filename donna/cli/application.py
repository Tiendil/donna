import typer

from donna.cli.entities import GLOBAL_OPTIONS_CONTEXT_KEY, GlobalOptions
from donna.cli.types import ProtocolModeOption, RootOption
from donna.protocol.modes import Mode

app = typer.Typer(help="Donna CLI: manage hierarchical state machines to guide your AI agents.")


@app.callback()
def initialize(
    context: typer.Context,
    protocol: ProtocolModeOption = Mode.human,
    root_dir: RootOption = None,
) -> None:
    context.meta[GLOBAL_OPTIONS_CONTEXT_KEY] = GlobalOptions(protocol=protocol, root_dir=root_dir)
