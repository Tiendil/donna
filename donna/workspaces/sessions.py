import os
import pathlib
import shutil
import stat
import time
from collections.abc import Iterable

from donna.workspaces.config import DONNA_DIR_NAME, DONNA_WORLD_SESSION_DIR_NAME, project_dir


def dir() -> pathlib.Path:
    return project_dir() / DONNA_DIR_NAME / DONNA_WORLD_SESSION_DIR_NAME


def ensure_dir() -> None:
    dir().mkdir(parents=True, exist_ok=True)


def reset_dir() -> None:
    session_dir = dir()
    if session_dir.exists():
        shutil.rmtree(session_dir)

    ensure_dir()


def read_state() -> bytes | None:
    path = dir() / "state.json"
    if not path.exists():
        return None

    return path.read_bytes()


def write_state(content: bytes) -> None:
    path = dir() / "state.json"
    ensure_dir()
    path.write_bytes(content)


def reset_journal() -> None:
    path = dir() / "journal.jsonl"
    ensure_dir()
    path.write_bytes(b"")


def append_journal_record(content: bytes) -> None:
    path = dir() / "journal.jsonl"
    ensure_dir()

    with path.open("ab") as stream:
        stream.write(content.rstrip(b"\n"))
        stream.write(b"\n")


def read_journal(lines: int | None = None, follow: bool = False) -> Iterable[bytes]:
    path = dir() / "journal.jsonl"

    yield from _journal_read_some(path, lines=lines)

    if not follow:
        return

    yield from _journal_follow(path)


def _journal_read_all(path: pathlib.Path) -> list[bytes]:
    if not path.exists():
        return []

    with path.open("rb") as stream:
        return [line.rstrip(b"\n") for line in stream if line.strip()]


def _journal_file_identity(path: pathlib.Path) -> tuple[int, int] | None:
    try:
        path_stat = path.stat()
    except FileNotFoundError:
        return None

    if not stat.S_ISREG(path_stat.st_mode):
        return None

    return (path_stat.st_dev, path_stat.st_ino)


def _journal_read_some(path: pathlib.Path, lines: int | None = None) -> Iterable[bytes]:
    records = _journal_read_all(path)

    if lines is not None:
        records = records[-lines:] if lines > 0 else []

    yield from records


def _journal_follow(path: pathlib.Path, poll_interval: float = 0.25) -> Iterable[bytes]:  # noqa: CCR001
    stream = None
    stream_identity: tuple[int, int] | None = None
    start_from_head = False

    while True:
        file_identity = _journal_file_identity(path)

        if stream is not None and stream_identity != file_identity:
            stream.close()
            stream = None
            stream_identity = None

        if file_identity is None or file_identity == stream_identity:
            start_from_head = True

        if stream is None and file_identity is not None:
            stream = path.open("rb")

            if not start_from_head:
                stream.seek(0, os.SEEK_END)

            stream_identity = file_identity

        if stream is None:
            time.sleep(poll_interval)
            continue

        while line := stream.readline():
            line = line.rstrip(b"\n")
            if line.strip():
                yield line

        time.sleep(poll_interval)
