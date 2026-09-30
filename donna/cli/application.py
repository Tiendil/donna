import typer
from llm_tool_cli.cli.context import set_global_options
from llm_tool_cli.cli.entities import GlobalOptions
from llm_tool_cli.cli.options import ConfigOption

from donna.cli.types import ProtocolModeOption

app = typer.Typer(help="Donna CLI: manage hierarchical state machines to guide your AI agents.")


@app.callback()
def initialize(
    context: typer.Context,
    protocol: ProtocolModeOption = None,
    config_path: ConfigOption = None,
) -> None:
    set_global_options(
        context,
        GlobalOptions(protocol=protocol, config_path=config_path),
    )


def main() -> None:
    from donna.cli.commands import artifacts  # noqa: F401
    from donna.cli.commands import sessions  # noqa: F401
    from donna.cli.commands import skills  # noqa: F401
    from donna.cli.commands import version  # noqa: F401
    from donna.cli.commands import workspaces  # noqa: F401

    app()
