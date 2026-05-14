import datetime
import pathlib

from donna.core import errors as core_errors
from donna.core.result import Err, Ok, Result


def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def first_project_dir_with_config(config_name: str) -> pathlib.Path | None:
    """Get the first parent directory containing the Donna config file.

    Search from the current working directory upwards for a folder with Donna config.
    """
    current_dir = pathlib.Path.cwd().resolve()

    for parent in [current_dir] + list(current_dir.parents):
        config_path = parent / config_name
        if config_path.is_file():
            return parent

    return None


def discover_project_dir(config_name: str) -> Result[pathlib.Path, core_errors.ErrorsList]:
    """Discover the project directory by looking for the Donna config file in parent folders."""
    project_dir = first_project_dir_with_config(config_name)

    if project_dir is None:
        return Err([core_errors.ProjectDirNotFound(config_name=config_name)])

    return Ok(project_dir)
