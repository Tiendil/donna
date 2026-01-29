import tomllib

from donna.core import errors as core_errors
from donna.core import utils
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.world import config
from donna.world import errors as world_errors


@unwrap_to_error
def initialize_environment() -> Result[None, core_errors.ErrorsList]:
    """Initialize the environment for the application.

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
        # return list of Environment errors
        return Err([world_errors.ConfigParseFailed(config_path=config_path, details=str(e))])

    try:
        loaded_config = config.Config.model_validate(data)
    except Exception as e:
        # return list of Environment errors
        return Err([world_errors.ConfigValidationFailed(config_path=config_path, details=str(e))])

    config.config.set(loaded_config)

    return Ok(None)
