import pathlib
from functools import lru_cache
from typing import TYPE_CHECKING

from donna.core.errors import ErrorsList
from donna.core.entities import BaseEntity
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.artifact_ids import ArtifactId, ArtifactIdPattern
from donna.domain.id_paths import NormalizedRawIdPath
from donna.domain.types import Milliseconds
from donna.machine.tasks import Task, WorkUnit
from donna.workspaces import errors as world_errors
from donna.workspaces.templates import RenderMode

if TYPE_CHECKING:
    from donna.machine.artifacts import Artifact


class ArtifactRenderContext(BaseEntity):
    primary_mode: RenderMode
    current_task: Task | None = None
    current_work_unit: WorkUnit | None = None


RENDER_CONTEXT_VIEW = ArtifactRenderContext(primary_mode=RenderMode.view)


class FilesystemRawArtifact(BaseEntity):
    source_id: str
    path: pathlib.Path

    def get_bytes(self) -> bytes:
        return self.path.read_bytes()

    @unwrap_to_error
    def render(
        self, artifact_id: ArtifactId, render_context: ArtifactRenderContext
    ) -> Result["Artifact", ErrorsList]:
        return Ok(render_artifact_from_source(artifact_id, self.source_id, self.get_bytes(), render_context).unwrap())


def _should_skip_directory(parts: list[str], name: str) -> bool:
    # `.donna/tmp` contains scratch files and must not be treated as durable artifacts.
    return parts == [".donna"] and name == "tmp"


def list_artifact_ids(pattern: ArtifactIdPattern) -> list[ArtifactId]:  # noqa: CCR001
    from donna.workspaces.config import config, project_dir

    root = project_dir()

    if not root.exists() or not root.is_dir():
        return []

    pattern_parts = tuple(pattern)
    supported_extensions = config().supported_extensions()
    artifacts: set[ArtifactId] = set()

    def walk(node: pathlib.Path, parts: list[str]) -> None:
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

            extension = entry.suffix.lower()
            if extension not in supported_extensions:
                continue

            artifact_parts = parts + [entry.name]
            artifact_name = "/".join(artifact_parts)
            if not ArtifactId.validate(artifact_name):
                continue

            artifact_id = ArtifactId(NormalizedRawIdPath(artifact_name))
            if pattern.matches(artifact_id):
                artifacts.add(artifact_id)

    walk(root, [])

    return list(sorted(artifacts))


def resolve_artifact_path(artifact_id: ArtifactId) -> Result[pathlib.Path | None, ErrorsList]:
    from donna.workspaces.config import project_dir

    artifact_path = project_dir().joinpath(*artifact_id.parts)
    if not artifact_path.parent.exists():
        return Ok(None)

    if not artifact_path.exists() or not artifact_path.is_file():
        return Ok(None)

    return Ok(artifact_path)


@unwrap_to_error
def fetch_artifact_bytes(artifact_id: ArtifactId) -> Result[tuple[str, bytes], ErrorsList]:
    raw_artifact = fetch_raw_artifact(artifact_id).unwrap()
    return Ok((raw_artifact.source_id, raw_artifact.get_bytes()))


@unwrap_to_error
def fetch_raw_artifact(artifact_id: ArtifactId) -> Result[FilesystemRawArtifact, ErrorsList]:
    from donna.workspaces.config import config

    artifact_path = resolve_artifact_path(artifact_id).unwrap()
    if artifact_path is None:
        return Err([world_errors.ArtifactNotFound(artifact_id=artifact_id)])

    source_config = config().find_source_for_extension(artifact_path.suffix)
    if source_config is None:
        return Err(
            [
                world_errors.UnsupportedArtifactSourceExtension(
                    artifact_id=artifact_id,
                    extension=artifact_path.suffix,
                )
            ]
        )

    return Ok(
        FilesystemRawArtifact(
            source_id=source_config.kind,
            path=artifact_path,
        )
    )


@unwrap_to_error
def render_artifact_from_source(
    artifact_id: ArtifactId,
    source_id: str,
    content: bytes,
    render_context: ArtifactRenderContext,
) -> Result["Artifact", ErrorsList]:
    from donna.workspaces.config import config

    source_config = config().get_source_config(source_id).unwrap()
    return Ok(source_config.construct_artifact_from_bytes(artifact_id, content, render_context).unwrap())


@unwrap_to_error
def has_artifact_changed(artifact_id: ArtifactId, since: Milliseconds) -> Result[bool, ErrorsList]:
    artifact_path = resolve_artifact_path(artifact_id).unwrap()

    if artifact_path is None:
        return Ok(True)

    return Ok((artifact_path.stat().st_mtime_ns // 1_000_000) > since)


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
