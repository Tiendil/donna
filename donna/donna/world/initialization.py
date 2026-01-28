import tomllib

from donna.core import errors as core_errors
from donna.core import utils
from donna.core.result import Err, Ok, Result
from donna.world import config


def initialize_environment() -> Result[None, core_errors.ErrorsList]:
    """Initialize the environment for the application.

    This function MUST be called before any other operations.
    """
    project_dir_result = utils.discover_project_dir(config.DONNA_DIR_NAME)

    if project_dir_result.is_err():
        return Err(project_dir_result.unwrap_err())

    project_dir = project_dir_result.unwrap()

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
        raise NotImplementedError(f"Failed to parse config file: {e}") from e

    try:
        loaded_config = config.Config.model_validate(data)
    except Exception as e:
        raise NotImplementedError(f"Failed to validate config file: {e}") from e

    config.config.set(loaded_config)

    return Ok(None)
