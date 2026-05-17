import pathlib

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.paths import ProjectRootPath
from donna.workspaces import errors as workspace_errors


def first_project_dir_with_config(config_name: str) -> ProjectRootPath | None:
    current_dir = pathlib.Path.cwd().resolve()

    for parent in [current_dir] + list(current_dir.parents):
        config_path = parent / config_name
        if config_path.is_file():
            return ProjectRootPath(parent)

    return None


def discover_project_dir(config_name: str) -> Result[ProjectRootPath, ErrorsList]:
    project_dir = first_project_dir_with_config(config_name)

    if project_dir is None:
        return Err([workspace_errors.WorkspaceConfigNotDiscovered(config_name=config_name)])

    return Ok(project_dir)
