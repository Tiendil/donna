import importlib.resources
import pathlib
import tomllib

from donna.core import errors as core_errors
from donna.core import utils
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.constants import DONNA_CONFIG_NAME
from donna.domain.paths import PathInput, ProjectConfigPath, ProjectRootPath, UntrustedPath
from donna.protocol.modes import Mode
from donna.workspaces import config
from donna.workspaces import errors as world_errors
from donna.workspaces.paths import resolve_project_root

BASE_CONFIG_FIXTURE = "base_config.toml"


@unwrap_to_error
def load_workspace(root_dir: PathInput | None = None) -> Result[config.Workspace, core_errors.ErrorsList]:
    """Load workspace configuration without mutating process-global state."""
    if root_dir is None:
        project_dir = utils.discover_project_dir(DONNA_CONFIG_NAME).unwrap()
    else:
        project_dir = resolve_project_root(UntrustedPath(root_dir))
        if not (pathlib.Path(project_dir) / DONNA_CONFIG_NAME).is_file():
            return Err([core_errors.ProjectDirNotFound(config_name=DONNA_CONFIG_NAME)])

    config_path = ProjectConfigPath(pathlib.Path(project_dir) / DONNA_CONFIG_NAME)

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
    root_dir: PathInput | None = None,
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
def initialize_workspace(project_dir: PathInput) -> Result[config.Workspace, core_errors.ErrorsList]:
    """Initialize Donna project configuration."""
    project_dir = ProjectRootPath(pathlib.Path(project_dir).resolve())
    config_path = ProjectConfigPath(pathlib.Path(project_dir) / DONNA_CONFIG_NAME)

    if config_path.exists():
        return Err([world_errors.WorkspaceAlreadyInitialized(config_path=config_path)])

    config_text = (
        importlib.resources.files(__package__).joinpath("fixtures", BASE_CONFIG_FIXTURE).read_text(encoding="utf-8")
    )
    config_path.write_text(config_text, encoding="utf-8")

    workspace = load_workspace(root_dir=project_dir).unwrap()
    config.install_workspace(workspace)

    return Ok(workspace)
