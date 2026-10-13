from pathlib import Path

import typer
from llm_tool_cli.config import initialize_project
from llm_tool_cli.config.project import project_config
from llm_tool_cli.output import output
from llm_tool_cli.paths import PathInput
from llm_tool_cli.protocol.cell_shortcuts import configuration_created

from donna.cli.application import app
from donna.cli.utils import command_context
from donna.workspaces.config import Config


@app.command(help="Initialize Donna project config.")
def init(context: typer.Context) -> None:
    with command_context(context, load_environment=False) as command:
        context.with_resource(
            initialize_project(
                Config,
                package="donna.workspaces",
                template="base_config.toml",
                cwd=PathInput(Path.cwd()),
                path=command.config_input,
            )
        ).unwrap()
        output.get().emit([configuration_created(project_config.get().config_path)]).unwrap()
