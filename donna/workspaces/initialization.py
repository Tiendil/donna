import tomllib
import pathlib
import tomli_w

from donna.core import errors as core_errors
from donna.core import utils
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.workspaces import config
from donna.workspaces import errors as world_errors
from donna.domain.ids import WorldId


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
        data = tomllib.loads(config_path.read_text())
    except tomllib.TOMLDecodeError as e:
        return Err([world_errors.ConfigParseFailed(config_path=config_path, details=str(e))])

    try:
        loaded_config = config.Config.model_validate(data)
    except Exception as e:
        return Err([world_errors.ConfigValidationFailed(config_path=config_path, details=str(e))])

    config.config.set(loaded_config)

    return Ok(None)


@unwrap_to_error
def initialzie_workspace(project_dir: pathlib.Path) -> Result[None, core_errors.ErrorsList]:
    """Initialize the physical workspace for the project (`.donna` directory).
    """

    existed_project_dir_result = utils.discover_project_dir(config.DONNA_DIR_NAME)

    if existed_project_dir_result.is_ok() and existed_project_dir_result.unwrap() == project_dir:
        return Err([world_errors.WorkspaceAlreadyInitialized(project_dir=project_dir)])

    config.config_dir().mkdir(parents=True, exist_ok=True)

    default_config = config.config()

    with open(config.config_dir() / config.DONNA_CONFIG_NAME, "w") as f:
        f.write(tomli_w.dumps(default_config.model_dump()))

    project = default_config().get_world(WorldId("project")).unwrap()

    project.initialize()

    session = default_config().get_world(WorldId("session")).unwrap()

    session.initialize()
