import pathlib
from typing import TYPE_CHECKING, Iterator, Sequence

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.artifact_ids import ArtifactId, artifact_path_parts, validate_artifact_id
from donna.domain.constants import DONNA_ARTIFACT_EXTENSION
from donna.domain.paths import ProjectPathId, RelativeProjectPath, ResolvedProjectPath, UntrustedPath
from donna.domain.types import Milliseconds
from donna.machine.tasks import Task, WorkUnit
from donna.workspaces import errors as world_errors
from donna.workspaces.paths import normalize_existing_path
from donna.workspaces.templates import RenderMode

if TYPE_CHECKING:
    from donna.machine.artifacts import Artifact


class ArtifactRenderContext(BaseEntity):
    primary_mode: RenderMode
    current_task: Task | None = None
    current_work_unit: WorkUnit | None = None


RENDER_CONTEXT_VIEW = ArtifactRenderContext(primary_mode=RenderMode.view)


class FilesystemRawArtifact(BaseEntity):
    path: ResolvedProjectPath

    def get_bytes(self) -> bytes:
        return pathlib.Path(self.path).read_bytes()

    @unwrap_to_error
    def render(self, artifact_id: ArtifactId, render_context: ArtifactRenderContext) -> Result["Artifact", ErrorsList]:
        return Ok(render_markdown_artifact(artifact_id, self.get_bytes(), render_context).unwrap())


def has_donna_artifact_extension(path: ProjectPathId | RelativeProjectPath | ResolvedProjectPath | str) -> bool:
    return pathlib.PurePath(path).name.lower().endswith(DONNA_ARTIFACT_EXTENSION)


def _artifact_id_from_parts(parts: Sequence[str]) -> ArtifactId | None:
    artifact_name = "@/" + "/".join(parts)
    if not validate_artifact_id(artifact_name):
        return None

    return ArtifactId(artifact_name)


def _workflow_dir_parts(path: RelativeProjectPath) -> tuple[str, ...]:
    return pathlib.PurePosixPath(path.as_posix()).parts


def _artifact_is_in_workflow_dirs(artifact_id: ArtifactId, workflow_dirs: Sequence[RelativeProjectPath]) -> bool:
    artifact_parts = artifact_path_parts(artifact_id)

    for workflow_dir in workflow_dirs:
        workflow_parts = _workflow_dir_parts(workflow_dir)
        if len(artifact_parts) <= len(workflow_parts):
            continue

        if artifact_parts[: len(workflow_parts)] == workflow_parts:
            return True

    return False


def _artifact_is_visible_in_workspace(artifact_id: ArtifactId) -> bool:
    from donna.workspaces import config as workspace_config

    return _artifact_is_in_workflow_dirs(artifact_id, workspace_config.config().workflow_dirs)


def _artifact_id_from_filesystem_entry(entry: ResolvedProjectPath, parts: list[str]) -> ArtifactId | None:
    if not entry.is_file():
        return None

    if not has_donna_artifact_extension(entry):
        return None

    artifact_parts = parts + [entry.name]
    return _artifact_id_from_parts(artifact_parts)


def _walk_workflow_dir(node: ResolvedProjectPath, parts: list[str]) -> Iterator[ArtifactId]:
    for raw_entry in sorted(pathlib.Path(node).iterdir(), key=lambda item: item.name):
        entry = ResolvedProjectPath(raw_entry)
        if entry.is_dir():
            yield from _walk_workflow_dir(entry, parts + [entry.name])
            continue

        artifact_id = _artifact_id_from_filesystem_entry(entry, parts)
        if artifact_id is not None:
            yield artifact_id


def walk_filesystem(workflow_dirs: Sequence[RelativeProjectPath]) -> Iterator[ArtifactId]:
    from donna.workspaces.config import project_dir

    root = project_dir()
    if not root.exists() or not root.is_dir():
        return

    for workflow_dir in workflow_dirs:
        workflow_parts = _workflow_dir_parts(workflow_dir)
        workflow_path = root.joinpath(*workflow_parts)
        if not workflow_path.exists() or not workflow_path.is_dir():
            continue

        yield from _walk_workflow_dir(ResolvedProjectPath(workflow_path), list(workflow_parts))


def list_artifact_ids() -> list[ArtifactId]:
    from donna.workspaces import config as workspace_config

    artifacts: list[ArtifactId] = []
    seen: set[ArtifactId] = set()

    for artifact_id in walk_filesystem(workspace_config.config().workflow_dirs):
        if artifact_id in seen:
            continue

        artifacts.append(artifact_id)
        seen.add(artifact_id)

    return artifacts


def resolve_artifact_path(artifact_id: ArtifactId) -> Result[ResolvedProjectPath | None, ErrorsList]:
    from donna.workspaces.config import project_dir

    artifact_path = project_dir().joinpath(*artifact_path_parts(artifact_id))
    if not artifact_path.parent.exists():
        return Ok(None)

    if not artifact_path.exists() or not artifact_path.is_file():
        return Ok(None)

    if normalize_existing_path(UntrustedPath(artifact_path), UntrustedPath(project_dir())) is None:
        return Ok(None)

    return Ok(ResolvedProjectPath(artifact_path))


@unwrap_to_error
def fetch_artifact_bytes(artifact_id: ArtifactId) -> Result[bytes, ErrorsList]:
    raw_artifact = fetch_raw_artifact(artifact_id).unwrap()
    return Ok(raw_artifact.get_bytes())


@unwrap_to_error
def fetch_raw_artifact(artifact_id: ArtifactId) -> Result[FilesystemRawArtifact, ErrorsList]:
    if not _artifact_is_visible_in_workspace(artifact_id):
        return Err([world_errors.ArtifactNotFound(artifact_id=artifact_id)])

    artifact_path = resolve_artifact_path(artifact_id).unwrap()
    if artifact_path is None:
        return Err([world_errors.ArtifactNotFound(artifact_id=artifact_id)])

    if not has_donna_artifact_extension(artifact_path):
        return Err(
            [
                world_errors.UnsupportedArtifactExtension(
                    artifact_id=artifact_id,
                    extension="".join(artifact_path.suffixes).lower() or artifact_path.suffix.lower(),
                )
            ]
        )

    return Ok(
        FilesystemRawArtifact(
            path=artifact_path,
        )
    )


@unwrap_to_error
def render_markdown_artifact(
    artifact_id: ArtifactId,
    content: bytes,
    render_context: ArtifactRenderContext,
) -> Result["Artifact", ErrorsList]:
    from donna.workspaces.config import config
    from donna.workspaces.markdown_parser import construct_artifact_from_bytes

    workspace_config = config()
    return Ok(
        construct_artifact_from_bytes(
            artifact_id,
            content,
            render_context,
            default_section_kind=workspace_config.default_section_kind,
            default_primary_section_kind=workspace_config.default_primary_section_kind,
            default_primary_section_id=workspace_config.default_primary_section_id,
        ).unwrap()
    )


@unwrap_to_error
def has_artifact_changed(artifact_id: ArtifactId, since: Milliseconds) -> Result[bool, ErrorsList]:
    artifact_path = resolve_artifact_path(artifact_id).unwrap()

    if artifact_path is None:
        return Ok(True)

    return Ok((artifact_path.stat().st_mtime_ns // 1_000_000) > since)
