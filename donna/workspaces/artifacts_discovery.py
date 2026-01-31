import pathlib
from functools import lru_cache
from typing import Iterable, Protocol

from donna.domain.ids import ArtifactId, FullArtifactId, FullArtifactIdPattern, WorldId
from donna.workspaces.config import config


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
) -> list[ArtifactId]:
    if pattern[0] not in {"*", "**"} and pattern[0] != str(world_id):
        return []

    if root is None or not root.is_dir():
        return []

    pattern_parts = tuple(pattern)
    world_prefix = (str(world_id),)
    supported_extensions = config().supported_extensions()
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
