import pathlib
from functools import lru_cache
from typing import Iterable, Protocol

from donna.domain.artifact_ids import ArtifactId, ArtifactIdPattern
from donna.workspaces.config import config


def _should_skip_directory(parts: list[str], name: str) -> bool:
    # `.donna/tmp` holds scratch files produced during artifact editing and verification.
    # Once the project world is rooted at `<project-root>`, those files must not appear as durable artifacts.
    return parts == [".donna"] and name == "tmp"


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
    root: ArtifactListingNode | None,
    pattern: ArtifactIdPattern,
) -> list[ArtifactId]:
    if root is None or not root.is_dir():
        return []

    pattern_parts = tuple(pattern)
    supported_extensions = config().supported_extensions()
    artifacts: set[ArtifactId] = set()

    def walk(node: ArtifactListingNode, parts: list[str]) -> None:  # noqa: CCR001
        for entry in sorted(node.iterdir(), key=lambda item: item.name):
            if entry.is_dir():
                if _should_skip_directory(parts, entry.name):
                    continue

                next_parts = parts + [entry.name]
                if not _pattern_allows_prefix(pattern_parts, tuple(next_parts)):
                    continue
                walk(entry, next_parts)
                continue

            if not entry.is_file():
                continue

            extension = pathlib.Path(entry.name).suffix.lower()
            if extension not in supported_extensions:
                continue

            # `parts` are always relative to the configured world root.
            # When the default project world is rooted at `<project-root>`,
            # this naturally produces ids under `specs`, `.agents/donna`, and `.donna/session`.
            artifact_parts = parts + [pathlib.Path(entry.name).stem]
            artifact_name = ":".join(artifact_parts)
            if ArtifactId.validate(artifact_name):
                artifact_id = ArtifactId(artifact_name)
                if pattern.matches(artifact_id):
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
