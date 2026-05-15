import pathlib
import tomllib

import tomli_w

from donna.core import errors as core_errors
from donna.core import utils
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.protocol.modes import Mode
from donna.workspaces import config
from donna.workspaces import errors as world_errors
from donna.workspaces import sessions as workspace_sessions


@unwrap_to_error
def load_workspace(root_dir: pathlib.Path | None = None) -> Result[config.Workspace, core_errors.ErrorsList]:
    """Load workspace configuration without mutating process-global state."""
    if root_dir is None:
        project_dir = utils.discover_project_dir(config.DONNA_CONFIG_NAME).unwrap()
    else:
        project_dir = root_dir.resolve()
        if not (project_dir / config.DONNA_CONFIG_NAME).is_file():
            return Err([core_errors.ProjectDirNotFound(config_name=config.DONNA_CONFIG_NAME)])

    config_path = project_dir / config.DONNA_CONFIG_NAME

    if not config_path.exists():
        return Ok(config.Workspace(root=project_dir, config=config.Config()))

    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        return Err([world_errors.ConfigParseFailed(config_path=config_path, details=str(e))])

    try:
        loaded_config = config.Config.model_validate(data)
    except Exception as e:
        return Err([world_errors.ConfigValidationFailed(config_path=config_path, details=str(e))])

    return Ok(config.Workspace(root=project_dir, config=loaded_config))


@unwrap_to_error
def initialize_runtime(
    root_dir: pathlib.Path | None = None,
    protocol: Mode | None = None,
) -> Result[config.Workspace, core_errors.ErrorsList]:
    """Initialize the runtime environment for the application.

    This function MUST be called before any other operations.
    """
    if protocol is not None:
        config.protocol.set(protocol)

    workspace = load_workspace(root_dir=root_dir).unwrap()
    config.install_workspace(workspace)

    return Ok(workspace)


@unwrap_to_error
def initialize_workspace(project_dir: pathlib.Path) -> Result[config.Workspace, core_errors.ErrorsList]:
    """Initialize Donna project configuration."""
    project_dir = project_dir.resolve()
    config_path = project_dir / config.DONNA_CONFIG_NAME

    if config_path.exists():
        return Err([world_errors.WorkspaceAlreadyInitialized(config_path=config_path)])

    default_config = config.Config()
    workspace = config.Workspace(root=project_dir, config=default_config)
    config.install_workspace(workspace)

    config_path.write_text(
        tomli_w.dumps(default_config.model_dump(mode="json", exclude_none=True)),
        encoding="utf-8",
    )

    workspace_sessions.ensure_dir()

    return Ok(workspace)
