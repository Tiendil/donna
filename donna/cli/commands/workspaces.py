import typer

from donna.cli.application import app
from donna.cli.utils import command_context
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.workspaces.initialization import initialize_workspace


@app.command(help="Initialize Donna project config.")
def init(context: typer.Context) -> None:
    with command_context(context, load_environment=False) as command:
        config_path = command.target_config_path()

        initialize_workspace(config_path).unwrap()

        command.write_cells([operation_succeeded("Donna project initialized successfully")])
