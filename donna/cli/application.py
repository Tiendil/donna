import typer

from donna.cli.types import ProtocolModeOption, RootOption
from donna.cli.utils import try_initialize_donna
from donna.protocol.modes import Mode

app = typer.Typer(help="Donna CLI: manage hierarchical state machines to guide your AI agents.")


@app.callback()
def initialize(
    protocol: ProtocolModeOption = Mode.human,
    root_dir: RootOption = None,
) -> None:
    try_initialize_donna(project_dir=root_dir, protocol=protocol)
