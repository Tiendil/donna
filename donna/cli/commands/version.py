import importlib.metadata

import typer
from llm_tool_cli.protocol import cell_shortcuts

from donna.cli.application import app
from donna.cli.utils import command_context


@app.command(help="Print the current Donna package version.")
def version(context: typer.Context) -> None:
    with command_context(context, load_environment=False) as command:
        command.write_cells([cell_shortcuts.version(importlib.metadata.version("donna"))])
