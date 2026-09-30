import typer
from llm_tool_cli.cli.entities import GlobalOptions
from llm_tool_cli.paths import ProjectConfigPath

from donna.cli.types import ConfigOption, ProtocolModeOption

GLOBAL_OPTIONS_CONTEXT_KEY = "donna_global_options"

app = typer.Typer(help="Donna CLI: manage hierarchical state machines to guide your AI agents.")


@app.callback()
def initialize(
    context: typer.Context,
    protocol: ProtocolModeOption = None,
    config_path: ConfigOption = None,
) -> None:
    context.meta[GLOBAL_OPTIONS_CONTEXT_KEY] = GlobalOptions(
        protocol=protocol, config_path=None if config_path is None else ProjectConfigPath(config_path)
    )


def main() -> None:
    from donna.cli.commands import artifacts  # noqa: F401
    from donna.cli.commands import sessions  # noqa: F401
    from donna.cli.commands import skills  # noqa: F401
    from donna.cli.commands import version  # noqa: F401
    from donna.cli.commands import workspaces  # noqa: F401

    app()
