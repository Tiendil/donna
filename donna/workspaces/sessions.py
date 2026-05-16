import pathlib
import shutil

from donna.domain.constants import STATE_FILE_NAME
from donna.workspaces.config import config, project_dir


def _path() -> pathlib.Path:
    return project_dir() / config().session_dir


def dir() -> pathlib.Path:
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
    path = dir() / STATE_FILE_NAME
    if not path.exists():
        return None

    return path.read_bytes()


def write_state(content: bytes) -> None:
    path = dir() / STATE_FILE_NAME
    path.write_bytes(content)
