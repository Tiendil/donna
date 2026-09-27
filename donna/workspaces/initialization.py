import importlib.resources
import pathlib

from llm_tool_cli.config import create_config, load_config, locate_config, resolve_config_path
from llm_tool_cli.core.result import Err, Ok, Result, unwrap_to_error
from llm_tool_cli.paths import PathInput
from llm_tool_cli.protocol import Protocol

from donna.domain.constants import DONNA_CONFIG_NAME
from donna.workspaces import config
from donna.workspaces import errors as world_errors

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
def initialize_workspace(config_path: PathInput) -> Result[config.Workspace]:
    """Initialize Donna project configuration."""
    selected_path = resolve_config_path(config_path, pathlib.Path.cwd()).unwrap()
    try:
        config_text = (
            importlib.resources.files(__package__)
            .joinpath("fixtures", BASE_CONFIG_FIXTURE)
            .read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError) as e:
        return Err([world_errors.ConfigCreateFailed(config_path=selected_path, details=str(e))])

    create_config(selected_path, config_text).unwrap()

    loaded_config = load_config(selected_path, config.Config).unwrap()
    workspace = config.construct_workspace(loaded_config, config_path=selected_path)
    config.install_workspace(workspace)

    return Ok(workspace)
