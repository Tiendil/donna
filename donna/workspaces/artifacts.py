import pathlib

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import FullArtifactId, FullArtifactIdPattern, WorldId
from donna.machine.artifacts import Artifact
from donna.machine.tasks import Task, WorkUnit
from donna.workspaces import errors
from donna.workspaces.config import config
from donna.workspaces.templates import RenderMode


class ArtifactRenderContext(BaseEntity):
    primary_mode: RenderMode
    current_task: Task | None = None
    current_work_unit: WorkUnit | None = None


class ArtifactUpdateError(errors.WorkspaceError):
    cell_kind: str = "artifact_update_error"
    artifact_id: FullArtifactId
    path: pathlib.Path

    def content_intro(self) -> str:
        return f"Error updating artifact '{self.artifact_id}' from the path '{self.path}'"


class CanNotUpdateReadonlyWorld(ArtifactUpdateError):
    code: str = "donna.workspaces.cannot_update_readonly_world"
    message: str = "Cannot upload artifact to the read-only world `{error.world_id}`"
    world_id: WorldId


class ArtifactRemoveError(errors.WorkspaceError):
    cell_kind: str = "artifact_remove_error"
    artifact_id: FullArtifactId

    def content_intro(self) -> str:
        return f"Error removing artifact '{self.artifact_id}'"


class CanNotRemoveReadonlyWorld(ArtifactRemoveError):
    code: str = "donna.workspaces.cannot_remove_readonly_world"
    message: str = "Cannot remove artifact from the read-only world `{error.world_id}`"
    world_id: WorldId


class InputPathHasNoExtension(ArtifactUpdateError):
    code: str = "donna.workspaces.input_path_has_no_extension"
    message: str = "Input path has no extension to determine artifact source type"


class NoSourceForArtifactExtension(ArtifactUpdateError):
    code: str = "donna.workspaces.no_source_for_artifact_extension"
    message: str = "No source found for artifact extension of input path"
    extension: str


class ArtifactCopyError(errors.WorkspaceError):
    cell_kind: str = "artifact_copy_error"
    source_id: FullArtifactId
    target_id: FullArtifactId

    def content_intro(self) -> str:
        return f"Error copying artifact '{self.source_id}' to '{self.target_id}'"


class CanNotCopyToReadonlyWorld(ArtifactCopyError):
    code: str = "donna.workspaces.cannot_copy_to_readonly_world"
    message: str = "Cannot copy artifact to the read-only world `{error.world_id}`"
    world_id: WorldId


class SourceArtifactHasNoExtension(ArtifactCopyError):
    code: str = "donna.workspaces.source_artifact_has_no_extension"
    message: str = "Source artifact has no extension to determine source type"


@unwrap_to_error
def artifact_file_extension(full_id: FullArtifactId) -> Result[str, ErrorsList]:
    world = config().get_world(full_id.world_id).unwrap()
    return Ok(world.file_extension_for(full_id.artifact_id).unwrap().lstrip("."))


@unwrap_to_error
def fetch_artifact(full_id: FullArtifactId, output: pathlib.Path) -> Result[None, ErrorsList]:
    world = config().get_world(full_id.world_id).unwrap()
    content = world.fetch_source(full_id.artifact_id).unwrap()

    with output.open("wb") as f:
        f.write(content)

    return Ok(None)


@unwrap_to_error
def update_artifact(full_id: FullArtifactId, input: pathlib.Path) -> Result[None, ErrorsList]:
    world = config().get_world(full_id.world_id).unwrap()

    if world.readonly:
        return Err([CanNotUpdateReadonlyWorld(artifact_id=full_id, path=input, world_id=world.id)])

    source_suffix = input.suffix.lower()
    content_bytes = input.read_bytes()

    if not source_suffix:
        return Err([InputPathHasNoExtension(artifact_id=full_id, path=input)])

    source_config = config().find_source_for_extension(source_suffix)
    if source_config is None:
        return Err([NoSourceForArtifactExtension(artifact_id=full_id, path=input, extension=source_suffix)])

    render_context = ArtifactRenderContext(primary_mode=RenderMode.view)
    test_artifact = source_config.construct_artifact_from_bytes(full_id, content_bytes, render_context).unwrap()
    validation_result = test_artifact.validate_artifact()

    validation_result.unwrap()
    world.update(full_id.artifact_id, content_bytes, source_suffix).unwrap()

    return Ok(None)


@unwrap_to_error
def copy_artifact(source_id: FullArtifactId, target_id: FullArtifactId) -> Result[None, ErrorsList]:
    source_world = config().get_world(source_id.world_id).unwrap()
    target_world = config().get_world(target_id.world_id).unwrap()

    if target_world.readonly:
        return Err(
            [
                CanNotCopyToReadonlyWorld(
                    source_id=source_id,
                    target_id=target_id,
                    world_id=target_world.id,
                )
            ]
        )

    content_bytes = source_world.fetch_source(source_id.artifact_id).unwrap()
    source_extension = source_world.file_extension_for(source_id.artifact_id).unwrap()

    if not source_extension:
        return Err([SourceArtifactHasNoExtension(source_id=source_id, target_id=target_id)])

    source_extension = source_extension.lower()
    source_config = config().find_source_for_extension(source_extension)
    if source_config is None:
        return Err(
            [
                NoSourceForArtifactExtension(
                    artifact_id=source_id,
                    path=pathlib.Path(str(source_id)),
                    extension=source_extension,
                )
            ]
        )

    render_context = ArtifactRenderContext(primary_mode=RenderMode.view)
    test_artifact = source_config.construct_artifact_from_bytes(target_id, content_bytes, render_context).unwrap()
    test_artifact.validate_artifact().unwrap()

    target_world.update(target_id.artifact_id, content_bytes, source_extension).unwrap()
    return Ok(None)


@unwrap_to_error
def move_artifact(source_id: FullArtifactId, target_id: FullArtifactId) -> Result[None, ErrorsList]:
    copy_result = copy_artifact(source_id, target_id)
    if copy_result.is_err():
        return copy_result

    return remove_artifact(source_id)


@unwrap_to_error
def remove_artifact(full_id: FullArtifactId) -> Result[None, ErrorsList]:
    world = config().get_world(full_id.world_id).unwrap()

    if world.readonly:
        return Err([CanNotRemoveReadonlyWorld(artifact_id=full_id, world_id=world.id)])

    world.remove(full_id.artifact_id).unwrap()
    return Ok(None)


@unwrap_to_error
def load_artifact(
    full_id: FullArtifactId, render_context: ArtifactRenderContext | None = None
) -> Result[Artifact, ErrorsList]:
    if render_context is None:
        render_context = ArtifactRenderContext(primary_mode=RenderMode.view)

    world = config().get_world(full_id.world_id).unwrap()
    return Ok(world.fetch(full_id.artifact_id, render_context).unwrap())


def list_artifacts(  # noqa: CCR001
    pattern: FullArtifactIdPattern,
    render_context: ArtifactRenderContext | None = None,
    tags: list[str] | None = None,
) -> Result[list[Artifact], ErrorsList]:
    if render_context is None:
        render_context = ArtifactRenderContext(primary_mode=RenderMode.view)

    tag_filters = tags or []

    artifacts: list[Artifact] = []
    errors: ErrorsList = []

    for world in reversed(config().worlds_instances):
        for artifact_id in world.list_artifacts(pattern):
            full_id = FullArtifactId((world.id, artifact_id))
            artifact_result = load_artifact(full_id, render_context)
            if artifact_result.is_err():
                errors.extend(artifact_result.unwrap_err())
                continue
            artifact = artifact_result.unwrap()
            if tag_filters and not _artifact_matches_tags(artifact, tag_filters):
                continue
            artifacts.append(artifact)

    if errors:
        return Err(errors)

    return Ok(artifacts)


def _artifact_matches_tags(artifact: Artifact, tags: list[str]) -> bool:
    if not tags:
        return True

    primary_result = artifact.primary_section()
    if primary_result.is_err():
        return False

    primary = primary_result.unwrap()
    return all(tag in primary.tags for tag in tags)
