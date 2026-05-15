import pathlib
import shutil

from donna.workspaces.config import config, project_dir

STATE_FILE_NAME = "state.json"


def dir() -> pathlib.Path:
    return project_dir() / config().session


def ensure_dir() -> None:
    dir().mkdir(parents=True, exist_ok=True)


def reset_dir() -> None:
    session_dir = dir()
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
    ensure_dir()
    path.write_bytes(content)
