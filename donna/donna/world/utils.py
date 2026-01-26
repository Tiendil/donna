import pathlib
import shutil
import time
from functools import lru_cache
from typing import Iterable, Protocol

from donna.cli.types import FullArtifactIdArgument
from donna.domain.ids import ArtifactId, FullArtifactId, FullArtifactIdPattern, WorldId
from donna.world.config import config, config_dir


class ArtifactListingNode(Protocol):
    name: str

    def is_dir(self) -> bool:
        """Return True when node is a directory."""
        ...

    def is_file(self) -> bool:
        """Return True when node is a file."""
        ...

    def iterdir(self) -> Iterable["ArtifactListingNode"]:
        """Iterate over child nodes."""
        ...


def list_artifacts_by_pattern(  # noqa: CCR001
    *,
    world_id: WorldId,
    root: ArtifactListingNode | None,
    pattern: FullArtifactIdPattern,
    supported_extensions: set[str],
) -> list[ArtifactId]:
    if pattern[0] not in {"*", "**"} and pattern[0] != str(world_id):
        return []

    if root is None or not root.is_dir():
        return []

    pattern_parts = tuple(pattern)
    world_prefix = (str(world_id),)
    artifacts: set[ArtifactId] = set()

    def walk(node: ArtifactListingNode, parts: list[str]) -> None:  # noqa: CCR001
        for entry in sorted(node.iterdir(), key=lambda item: item.name):
            if entry.is_dir():
                next_parts = parts + [entry.name]
                if not _pattern_allows_prefix(pattern_parts, world_prefix + tuple(next_parts)):
                    continue
                walk(entry, next_parts)
                continue

            if not entry.is_file():
                continue

            extension = pathlib.Path(entry.name).suffix.lower()
            if extension not in supported_extensions:
                continue

            stem = entry.name[: -len(extension)]
            artifact_name = ":".join(parts + [stem])
            if ArtifactId.validate(artifact_name):
                artifact_id = ArtifactId(artifact_name)
                full_id = FullArtifactId((world_id, artifact_id))
                if pattern.matches_full_id(full_id):
                    artifacts.add(artifact_id)

    walk(root, [])

    return list(sorted(artifacts))


def _pattern_allows_prefix(pattern_parts: tuple[str, ...], prefix_parts: tuple[str, ...]) -> bool:
    @lru_cache(maxsize=None)
    def match_at(p_index: int, v_index: int) -> bool:  # noqa: CCR001
        if v_index >= len(prefix_parts):
            return True

        if p_index >= len(pattern_parts):
            return False

        token = pattern_parts[p_index]

        if token == "**":  # noqa: S105
            return match_at(p_index + 1, v_index) or match_at(p_index, v_index + 1)

        if token == "*" or token == prefix_parts[v_index]:  # noqa: S105
            return match_at(p_index + 1, v_index + 1)

        return False

    return match_at(0, 0)


def tmp_dir() -> pathlib.Path:
    cfg = config()
    tmp_path = cfg.tmp_dir

    if not cfg.tmp_dir.is_absolute():
        tmp_path = config_dir() / tmp_path

    tmp_path.mkdir(parents=True, exist_ok=True)

    return tmp_path


def tmp_file_for_artifact(artifact_id: FullArtifactIdArgument, extention: str) -> pathlib.Path:
    directory = tmp_dir()

    directory.mkdir(parents=True, exist_ok=True)

    normalized_extension = extention.lstrip(".")
    artifact_file_name = f"{str(artifact_id).replace('/', '.')}.{int(time.time() * 1000)}.{normalized_extension}"

    return directory / artifact_file_name


def tmp_clear() -> None:
    shutil.rmtree(tmp_dir())
