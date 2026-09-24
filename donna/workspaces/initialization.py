import importlib.resources
import pathlib

from llm_tool_cli.config import create_config, load_config, locate_config, resolve_config_path
from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Err, Ok, Result, unwrap_to_error

from donna.domain.constants import DONNA_CONFIG_NAME
from donna.domain.paths import PathInput, ProjectConfigPath
from donna.protocol.modes import Mode
from donna.workspaces import config
from donna.workspaces import errors as world_errors

BASE_CONFIG_FIXTURE = "base_config.toml"


@unwrap_to_error
def initialize_runtime(
    config_path: PathInput | None = None,
    protocol: Mode | None = None,
) -> Result[config.Workspace, EnvironmentErrors]:
    """Initialize the runtime environment for the application.

    This function MUST be called before any other operations.
    """
    if protocol is not None:
        config.protocol.set(protocol)

    selected_path = ProjectConfigPath(
        locate_config(DONNA_CONFIG_NAME, path=config_path, cwd=pathlib.Path.cwd()).unwrap()
    )
    loaded_config = load_config(selected_path, config.Config).unwrap()
    workspace = config.construct_workspace(loaded_config, config_path=selected_path)
    config.install_workspace(workspace)

    return Ok(workspace)


@unwrap_to_error
def initialize_workspace(config_path: PathInput) -> Result[config.Workspace, EnvironmentErrors]:
    """Initialize Donna project configuration."""
    config_path = ProjectConfigPath(resolve_config_path(pathlib.Path(config_path), pathlib.Path.cwd()).unwrap())
    try:
        config_text = (
            importlib.resources.files(__package__)
            .joinpath("fixtures", BASE_CONFIG_FIXTURE)
            .read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError) as e:
        return Err([world_errors.ConfigCreateFailed(config_path=config_path, details=str(e))])

    create_config(pathlib.Path(config_path), config_text).unwrap()

    loaded_config = load_config(config_path, config.Config).unwrap()
    workspace = config.construct_workspace(loaded_config, config_path=config_path)
    config.install_workspace(workspace)

    return Ok(workspace)
