import glob
import pathlib
from typing import TYPE_CHECKING, Sequence

from llm_tool_cli.config.project import project_config
from llm_tool_cli.core.entities import BaseEntity
from llm_tool_cli.core.result import Err, Ok, Result, unwrap_to_error
from llm_tool_cli.paths import (
    FileGlobPattern,
    ProjectPathId,
    RelativeProjectPath,
    ResolvedProjectPath,
    enumerate_files,
    resolve_project_path,
)
from llm_tool_cli.paths.errors import InvalidProjectPath

from donna.domain.artifact_ids import ArtifactId, artifact_path_parts, validate_artifact_id
from donna.domain.constants import DONNA_ARTIFACT_EXTENSION
from donna.machine import ArtifactRenderContext
from donna.workspaces import errors as world_errors
from donna.workspaces.files import FileFingerprint

if TYPE_CHECKING:
    from donna.machine.artifacts import Artifact


class FilesystemRawArtifact(BaseEntity):
    path: ResolvedProjectPath

    def get_bytes(self) -> bytes:
        return pathlib.Path(self.path).read_bytes()

    @unwrap_to_error
    def render(self, artifact_id: ArtifactId, render_context: ArtifactRenderContext) -> Result["Artifact"]:
        return Ok(render_markdown_artifact(artifact_id, self.get_bytes(), render_context).unwrap())


def has_donna_artifact_extension(path: ProjectPathId | RelativeProjectPath | ResolvedProjectPath | str) -> bool:
    return pathlib.PurePath(path).name.lower().endswith(DONNA_ARTIFACT_EXTENSION)


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

    return _artifact_is_in_workflow_dirs(artifact_id, workspace_config.config.get().workflow_dirs)


@unwrap_to_error
def walk_filesystem(workflow_dirs: Sequence[RelativeProjectPath]) -> Result[list[ArtifactId]]:
    root = project_config.get().project_dir
    artifacts: list[ArtifactId] = []
    for workflow_dir in workflow_dirs:
        if workflow_dir.parts:
            resolve_project_path("@/" + workflow_dir.as_posix(), root).unwrap()
        pattern = FileGlobPattern("@/" + glob.escape(workflow_dir.as_posix()) + "/**/*")
        artifacts.extend(
            ArtifactId(path) for path in enumerate_files(root, pattern).unwrap() if validate_artifact_id(path)
        )
    return Ok(artifacts)


@unwrap_to_error
def list_artifact_ids() -> Result[list[ArtifactId]]:
    from donna.workspaces import config as workspace_config

    artifacts: list[ArtifactId] = []
    seen: set[ArtifactId] = set()

    for artifact_id in walk_filesystem(workspace_config.config.get().workflow_dirs).unwrap():
        if artifact_id in seen:
            continue

        artifacts.append(artifact_id)
        seen.add(artifact_id)

    return Ok(artifacts)


def resolve_artifact_path(artifact_id: ArtifactId) -> Result[ResolvedProjectPath | None]:
    root = project_config.get().project_dir
    resolved = resolve_project_path(artifact_id, root)
    if resolved.is_err(InvalidProjectPath):
        return Ok(None)
    if resolved.is_err():
        return resolved
    artifact_path = resolved.unwrap()
    if not artifact_path.is_file():
        return Ok(None)
    return Ok(artifact_path)


@unwrap_to_error
def fetch_artifact_bytes(artifact_id: ArtifactId) -> Result[bytes]:
    raw_artifact = fetch_raw_artifact(artifact_id).unwrap()
    return Ok(raw_artifact.get_bytes())


@unwrap_to_error
def fetch_raw_artifact(artifact_id: ArtifactId) -> Result[FilesystemRawArtifact]:
    if not _artifact_is_visible_in_workspace(artifact_id):
        return Err([world_errors.ArtifactNotFound(artifact_id=artifact_id)])

    artifact_path = resolve_artifact_path(artifact_id).unwrap()
    if artifact_path is None:
        return Err([world_errors.ArtifactNotFound(artifact_id=artifact_id)])

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
) -> Result["Artifact"]:
    from donna.workspaces import config as workspace_config
    from donna.workspaces.markdown_parser import construct_artifact_from_bytes

    defaults = workspace_config.config.get().defaults
    return Ok(
        construct_artifact_from_bytes(
            artifact_id,
            content,
            render_context,
            default_section_kind=defaults.tail_section_kind,
            default_primary_section_kind=defaults.primary_section_kind,
            default_primary_section_id=defaults.primary_section_id,
        ).unwrap()
    )


@unwrap_to_error
def artifact_fingerprint(artifact_id: ArtifactId) -> Result[FileFingerprint | None]:
    artifact_path = resolve_artifact_path(artifact_id).unwrap()

    if artifact_path is None:
        return Ok(None)

    return Ok(FileFingerprint.from_path(artifact_path))
