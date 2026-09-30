import typer
from llm_tool_cli.protocol.cell_shortcuts import configuration_created

from donna.cli.application import app
from donna.cli.utils import command_context
from donna.workspaces.initialization import initialize_workspace


@app.command(help="Initialize Donna project config.")
def init(context: typer.Context) -> None:
    with command_context(context, load_environment=False) as command:
        workspace = initialize_workspace(command.global_options.config_path).unwrap()

        command.write_cells([configuration_created(workspace.config_path)])
