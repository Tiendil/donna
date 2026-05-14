import typer

from donna.cli.application import app
from donna.cli.utils import command_context
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.workspaces.initialization import initialize_workspace, update_workspace

workspaces_cli = typer.Typer()


@workspaces_cli.command(help="Initialize Donna project config.")
def init(context: typer.Context) -> None:
    with command_context(context, load_environment=False) as command:
        target_dir = command.target_dir()

        initialize_workspace(target_dir).unwrap()

        command.write_cells([operation_succeeded("Donna project initialized successfully")])


@workspaces_cli.command(help="Update Donna project files.")
def update(context: typer.Context) -> None:
    with command_context(context) as command:
        target_dir = command.target_dir()

        update_workspace(target_dir).unwrap()

        command.write_cells([operation_succeeded("Donna project updated successfully")])


app.add_typer(
    workspaces_cli,
    name="workspaces",
    help="Initialize and manage Donna project files.",
)
