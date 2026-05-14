import importlib.resources
import pathlib
import shutil
import tomllib

import tomli_w

from donna.core import errors as core_errors
from donna.core import utils
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.protocol.modes import Mode
from donna.workspaces import config
from donna.workspaces import errors as world_errors
from donna.workspaces import sessions as workspace_sessions

SKILLS_ROOT_DIR = pathlib.Path(".agents") / "skills"
DONNA_SKILL_FIXTURE_DIR = pathlib.Path("fixtures") / "skills"
DONNA_SPECS_ROOT_DIR = pathlib.Path(".agents") / "donna"
DONNA_SPECS_FIXTURE_DIR = pathlib.Path("fixtures") / "specs"

# this list must only increase in size,
# do not remove old items from it, since users may upgrade from older versions of Donna
# where these skills were installed
DONNA_SKILL_CLEANUP_LIST = ["donna-do", "donna-start", "donna-stop"]


def _sync_donna_skill(project_dir: pathlib.Path) -> None:
    source = importlib.resources.files("donna").joinpath(*DONNA_SKILL_FIXTURE_DIR.parts)

    # cleanup
    for skill_id in DONNA_SKILL_CLEANUP_LIST:
        target_dir = project_dir / SKILLS_ROOT_DIR / skill_id
        if target_dir.exists():
            shutil.rmtree(target_dir)

    # copy all content of fixtures/skills to the skills directory
    with importlib.resources.as_file(source) as source_dir:
        shutil.copytree(source_dir, project_dir / SKILLS_ROOT_DIR, dirs_exist_ok=True)


def _sync_donna_specs(project_dir: pathlib.Path) -> None:
    source = importlib.resources.files("donna").joinpath(*DONNA_SPECS_FIXTURE_DIR.parts)
    target_dir = project_dir / DONNA_SPECS_ROOT_DIR

    if target_dir.exists():
        shutil.rmtree(target_dir)

    with importlib.resources.as_file(source) as source_dir:
        shutil.copytree(source_dir, target_dir)


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
def initialize_workspace(
    project_dir: pathlib.Path,
    install_skills: bool = True,
    install_specs: bool = True,
) -> Result[config.Workspace, core_errors.ErrorsList]:
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

    if install_skills:
        _sync_donna_skill(project_dir)

    if install_specs:
        _sync_donna_specs(project_dir)

    return Ok(workspace)


@unwrap_to_error
def update_workspace(
    project_dir: pathlib.Path,
    install_skills: bool = True,
    install_specs: bool = True,
) -> Result[None, core_errors.ErrorsList]:
    project_dir = project_dir.resolve()
    config_path = project_dir / config.DONNA_CONFIG_NAME

    if not config_path.exists():
        return Err([core_errors.ProjectDirNotFound(config_name=config.DONNA_CONFIG_NAME)])

    if install_skills:
        _sync_donna_skill(project_dir)

    if install_specs:
        _sync_donna_specs(project_dir)

    return Ok(None)
