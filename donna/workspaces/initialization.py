import importlib.resources
import pathlib
import shutil
import tomllib

import tomli_w

from donna.core import errors as core_errors
from donna.core import utils
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import WorldId
from donna.protocol.modes import Mode
from donna.workspaces import config
from donna.workspaces import errors as world_errors

SKILLS_ROOT_DIR = pathlib.Path(".agents") / "skills"
DONNA_SKILL_FIXTURE_DIR = pathlib.Path("fixtures") / "skills"

# this list must only increase in size,
# do not remove old items from it, since users may upgrade from older versions of Donna
# where these skills were installed
DONNA_SKILL_CLEANUP_LIST = ["donna", "donna-do", "donna-start", "donna-stop"]


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


@unwrap_to_error
def initialize_runtime(  # noqa: CCR001
    root_dir: pathlib.Path | None = None,
    protocol: Mode | None = None,
) -> Result[None, core_errors.ErrorsList]:
    """Initialize the runtime environment for the application.

    This function MUST be called before any other operations.
    """
    if protocol is not None:
        config.protocol.set(protocol)

    if root_dir is None:
        project_dir = utils.discover_project_dir(config.DONNA_DIR_NAME).unwrap()
    else:
        project_dir = root_dir.resolve()
        if not (project_dir / config.DONNA_DIR_NAME).is_dir():
            return Err([core_errors.ProjectDirNotFound(donna_dir_name=config.DONNA_DIR_NAME)])

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
def initialize_workspace(
    project_dir: pathlib.Path, install_skills: bool = True
) -> Result[None, core_errors.ErrorsList]:
    """Initialize the physical workspace for the project (`.donna` directory)."""
    project_dir = project_dir.resolve()
    workspace_dir = project_dir / config.DONNA_DIR_NAME

    if workspace_dir.exists():
        return Err([world_errors.WorkspaceAlreadyInitialized(project_dir=project_dir)])

    if not config.project_dir.is_set():
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

    if install_skills:
        _sync_donna_skill(project_dir)

    return Ok(None)


@unwrap_to_error
def update_workspace(project_dir: pathlib.Path, install_skills: bool = True) -> Result[None, core_errors.ErrorsList]:
    project_dir = project_dir.resolve()
    workspace_dir = project_dir / config.DONNA_DIR_NAME

    if not workspace_dir.exists():
        return Err([core_errors.ProjectDirNotFound(donna_dir_name=config.DONNA_DIR_NAME)])

    if install_skills:
        _sync_donna_skill(project_dir)

    return Ok(None)
