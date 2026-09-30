import pathlib

from llm_tool_cli.config import create_config_from_template, load_config, locate_config, resolve_init_config_path
from llm_tool_cli.core.result import Ok, Result, unwrap_to_error
from llm_tool_cli.paths import PathInput, ProjectConfigPath
from llm_tool_cli.protocol import Protocol

from donna.domain.constants import DONNA_CONFIG_NAME
from donna.workspaces import config

BASE_CONFIG_FIXTURE = "base_config.toml"


@unwrap_to_error
def initialize_runtime(
    config_path: PathInput | None = None,
    protocol: Protocol | None = None,
) -> Result[config.Workspace]:
    """Initialize the runtime environment for the application.

    This function MUST be called before any other operations.
    """
    if protocol is not None:
        config.protocol.set(protocol)

    selected_path = locate_config(DONNA_CONFIG_NAME, path=config_path, cwd=pathlib.Path.cwd()).unwrap()
    loaded_config = load_config(selected_path, config.Config).unwrap()
    workspace = config.construct_workspace(loaded_config, config_path=selected_path)
    config.install_workspace(workspace)

    return Ok(workspace)


@unwrap_to_error
def initialize_workspace(config_path: ProjectConfigPath | None = None) -> Result[config.Workspace]:
    """Initialize Donna project configuration."""
    selected_path = resolve_init_config_path(
        DONNA_CONFIG_NAME, path=config_path, cwd=PathInput(pathlib.Path.cwd())
    ).unwrap()
    create_config_from_template(selected_path, package=__package__, template=BASE_CONFIG_FIXTURE).unwrap()

    loaded_config = load_config(selected_path, config.Config).unwrap()
    workspace = config.construct_workspace(loaded_config, config_path=selected_path)
    config.install_workspace(workspace)

    return Ok(workspace)
