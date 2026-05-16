import typer

from donna.cli.entities import GLOBAL_OPTIONS_CONTEXT_KEY, GlobalOptions
from donna.cli.types import ProtocolModeOption, RootOption
from donna.domain.paths import UntrustedPath
from donna.protocol.modes import Mode

app = typer.Typer(help="Donna CLI: manage hierarchical state machines to guide your AI agents.")


@app.callback()
def initialize(
    context: typer.Context,
    protocol: ProtocolModeOption = Mode.human,
    root_dir: RootOption = None,
) -> None:
    context.meta[GLOBAL_OPTIONS_CONTEXT_KEY] = GlobalOptions(
        protocol=protocol, root_dir=None if root_dir is None else UntrustedPath(root_dir)
    )


def main() -> None:
    from donna.cli.commands import artifacts  # noqa: F401
    from donna.cli.commands import sessions  # noqa: F401
    from donna.cli.commands import skills  # noqa: F401
    from donna.cli.commands import version  # noqa: F401
    from donna.cli.commands import workspaces  # noqa: F401

    app()
