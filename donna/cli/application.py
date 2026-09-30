import typer
from llm_tool_cli.cli.context import set_global_options
from llm_tool_cli.cli.entities import GlobalOptions
from llm_tool_cli.cli.options import ConfigOption, ProtocolOption
from llm_tool_cli.core import settings

app = typer.Typer(help="Donna CLI: manage hierarchical state machines to guide your AI agents.")


@app.callback()
def initialize(
    context: typer.Context,
    protocol: ProtocolOption = None,
    config_path: ConfigOption = None,
) -> None:
    set_global_options(
        context,
        GlobalOptions(protocol=protocol, config_path=config_path),
    )


def main() -> None:
    settings.initialize(tool_label=settings.ToolLabel("DONNA"))

    from donna.cli.commands import artifacts  # noqa: F401
    from donna.cli.commands import sessions  # noqa: F401
    from donna.cli.commands import skills  # noqa: F401
    from donna.cli.commands import version  # noqa: F401
    from donna.cli.commands import workspaces  # noqa: F401

    app()
