import shutil

from llm_tool_cli.config.project import project_config
from llm_tool_cli.paths import ResolvedProjectPath

from donna.domain.constants import STATE_FILE_NAME
from donna.workspaces import config as workspace_config
from donna.workspaces.files import FileFingerprint


def _path() -> ResolvedProjectPath:
    project_dir = project_config.get().project_dir
    return ResolvedProjectPath(project_dir / workspace_config.config.get().session_dir)


def _state_path() -> ResolvedProjectPath:
    return ResolvedProjectPath(dir() / STATE_FILE_NAME)


def dir() -> ResolvedProjectPath:
    session_dir = _path()
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def ensure_dir() -> None:
    dir()


def reset_dir() -> None:
    session_dir = _path()
    if session_dir.exists():
        shutil.rmtree(session_dir)

    ensure_dir()


def read_state() -> bytes | None:
    path = _state_path()
    if not path.exists():
        return None

    return path.read_bytes()


def state_fingerprint() -> FileFingerprint | None:
    return FileFingerprint.from_path(_state_path())


def write_state(content: bytes) -> None:
    path = _state_path()
    path.write_bytes(content)
