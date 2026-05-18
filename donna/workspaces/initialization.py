import importlib.resources
import pathlib
import tomllib

from donna.core import errors as core_errors
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.constants import DONNA_CONFIG_NAME
from donna.domain.paths import PathInput, ProjectConfigPath, ProjectRootPath, UntrustedPath
from donna.protocol.modes import Mode
from donna.workspaces import config
from donna.workspaces import errors as world_errors
from donna.workspaces import utils
from donna.workspaces.paths import resolve_project_root

BASE_CONFIG_FIXTURE = "base_config.toml"


@unwrap_to_error
def load_workspace(config_path: PathInput | None = None) -> Result[config.Workspace, core_errors.ErrorsList]:
    """Load workspace configuration without mutating process-global state."""
    if config_path is None:
        project_dir = utils.discover_project_dir(DONNA_CONFIG_NAME).unwrap()
        resolved_config_path = ProjectConfigPath(pathlib.Path(project_dir) / DONNA_CONFIG_NAME)
    else:
        resolved_config_path = ProjectConfigPath(pathlib.Path(config_path).expanduser().resolve())
        project_dir = resolve_project_root(UntrustedPath(pathlib.Path(resolved_config_path).parent))

    if not pathlib.Path(resolved_config_path).is_file():
        return Err([world_errors.WorkspaceConfigNotFound(config_path=resolved_config_path)])

    try:
        data = pathlib.Path(resolved_config_path).read_text(encoding="utf-8")
        parsed = tomllib.loads(data)
    except tomllib.TOMLDecodeError as e:
        return Err([world_errors.ConfigParseFailed(config_path=resolved_config_path, details=str(e))])

    try:
        loaded_config = config.Config.model_validate(parsed)
    except Exception as e:
        return Err([world_errors.ConfigValidationFailed(config_path=resolved_config_path, details=str(e))])

    return Ok(config.Workspace(root=project_dir, config_path=resolved_config_path, config=loaded_config))


@unwrap_to_error
def initialize_runtime(
    config_path: PathInput | None = None,
    protocol: Mode | None = None,
) -> Result[config.Workspace, core_errors.ErrorsList]:
    """Initialize the runtime environment for the application.

    This function MUST be called before any other operations.
    """
    if protocol is not None:
        config.protocol.set(protocol)

    workspace = load_workspace(config_path=config_path).unwrap()
    config.install_workspace(workspace)

    return Ok(workspace)


@unwrap_to_error
def initialize_workspace(config_path: PathInput) -> Result[config.Workspace, core_errors.ErrorsList]:
    """Initialize Donna project configuration."""
    config_path = ProjectConfigPath(pathlib.Path(config_path).expanduser().resolve())
    project_dir = ProjectRootPath(pathlib.Path(config_path).parent)

    if not pathlib.Path(project_dir).is_dir():
        return Err([world_errors.WorkspaceConfigDirNotFound(config_path=config_path)])

    if pathlib.Path(config_path).exists():
        return Err([world_errors.WorkspaceAlreadyInitialized(config_path=config_path)])

    config_text = (
        importlib.resources.files(__package__).joinpath("fixtures", BASE_CONFIG_FIXTURE).read_text(encoding="utf-8")
    )
    pathlib.Path(config_path).write_text(config_text, encoding="utf-8")

    workspace = load_workspace(config_path=config_path).unwrap()
    config.install_workspace(workspace)

    return Ok(workspace)
