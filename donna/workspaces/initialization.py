import pathlib
import tomllib

import tomli_w

from donna.core import errors as core_errors
from donna.core import utils
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import WorldId
from donna.workspaces import config
from donna.workspaces import errors as world_errors


@unwrap_to_error
def initialize_runtime() -> Result[None, core_errors.ErrorsList]:
    """Initialize the runtime environment for the application.

    This function MUST be called before any other operations.
    """
    project_dir = utils.discover_project_dir(config.DONNA_DIR_NAME).unwrap()

    config.project_dir.set(project_dir)

    config_dir = project_dir / config.DONNA_DIR_NAME

    config.config_dir.set(config_dir)

    config_path = config_dir / config.DONNA_CONFIG_NAME

    if not config_path.exists():
        config.config.set(config.Config())
        return Ok(None)

    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        return Err([world_errors.ConfigParseFailed(config_path=config_path, details=str(e))])

    try:
        loaded_config = config.Config.model_validate(data)
    except Exception as e:
        return Err([world_errors.ConfigValidationFailed(config_path=config_path, details=str(e))])

    config.config.set(loaded_config)

    return Ok(None)


@unwrap_to_error
def initialize_workspace(project_dir: pathlib.Path) -> Result[None, core_errors.ErrorsList]:
    """Initialize the physical workspace for the project (`.donna` directory)."""
    project_dir = project_dir.resolve()
    workspace_dir = project_dir / config.DONNA_DIR_NAME

    if workspace_dir.exists():
        return Err([world_errors.WorkspaceAlreadyInitialized(project_dir=project_dir)])

    config.project_dir.set(project_dir)
    config.config_dir.set(workspace_dir)

    workspace_dir.mkdir(parents=True, exist_ok=True)

    default_config = config.Config()
    config.config.set(default_config)

    config_path = workspace_dir / config.DONNA_CONFIG_NAME
    config_path.write_text(
        tomli_w.dumps(default_config.model_dump(mode="json")),
        encoding="utf-8",
    )

    project_world = default_config.get_world(WorldId(config.DONNA_WORLD_PROJECT_DIR_NAME)).unwrap()
    project_world.initialize()

    session_world = default_config.get_world(WorldId(config.DONNA_WORLD_SESSION_DIR_NAME)).unwrap()
    session_world.initialize()

    return Ok(None)
