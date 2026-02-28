import pathlib

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import FullArtifactId, WorldId
from donna.machine.tasks import Task, WorkUnit
from donna.workspaces import errors
from donna.workspaces.config import config
from donna.workspaces.templates import RenderMode


class ArtifactRenderContext(BaseEntity):
    primary_mode: RenderMode
    current_task: Task | None = None
    current_work_unit: WorkUnit | None = None


RENDER_CONTEXT_VIEW = ArtifactRenderContext(primary_mode=RenderMode.view)


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


class ArtifactExtensionCannotBeInferred(ArtifactUpdateError):
    code: str = "donna.workspaces.artifact_extension_cannot_be_inferred"
    message: str = "Cannot infer artifact extension."
    ways_to_fix: list[str] = [
        "Pass `--extension <extension>` when updating the artifact.",
        "Provide an input path with extension (for example `*.md`).",
        "Update an artifact that already exists and has a known extension if that is applicable.",
    ]


class ArtifactExtensionMismatch(ArtifactUpdateError):
    code: str = "donna.workspaces.artifact_extension_mismatch"
    message: str = (
        "Provided extension `{error.provided_extension}` does not match existing artifact extension "
        "`{error.existing_extension}`"
    )
    provided_extension: str
    existing_extension: str
    ways_to_fix: list[str] = [
        "Use the existing artifact extension.",
        "Omit `--extension` to use extension inferred from the existing artifact.",
    ]


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
    raw_artifact = world.fetch(full_id.artifact_id).unwrap()

    with output.open("wb") as f:
        f.write(raw_artifact.get_bytes())

    return Ok(None)


@unwrap_to_error
def update_artifact(  # noqa: CCR001
    full_id: FullArtifactId, input: pathlib.Path, extension: str | None = None
) -> Result[None, ErrorsList]:
    world = config().get_world(full_id.world_id).unwrap()

    if world.readonly:
        return Err([CanNotUpdateReadonlyWorld(artifact_id=full_id, path=input, world_id=world.id)])

    content_bytes = input.read_bytes()

    expected_extension = artifact_file_extension(full_id).unwrap_or(None)

    requested_extension = extension.lstrip(".").lower() if extension is not None else None
    inferred_extension = input.suffix.lstrip(".").lower() or None

    def mismatch_error(a: str, b: str) -> Result[None, ErrorsList]:
        return Err(
            [
                ArtifactExtensionMismatch(
                    artifact_id=full_id,
                    path=input,
                    provided_extension=a,
                    existing_extension=b,
                )
            ]
        )

    match (expected_extension, requested_extension, inferred_extension):
        case (None, None, None):
            return Err([ArtifactExtensionCannotBeInferred(artifact_id=full_id, path=input)])

        case (None, None, inferred):
            source_suffix = inferred

        case (None, requested, None):
            source_suffix = requested

        case (None, requested, inferred) if requested == inferred:
            source_suffix = requested

        case (None, requested, inferred):
            assert requested is not None
            assert inferred is not None
            return mismatch_error(requested, inferred)

        case (expected, None, None):
            source_suffix = expected

        case (expected, None, inferred) if expected == inferred:
            source_suffix = expected

        case (expected, None, inferred):
            assert expected is not None
            assert inferred is not None
            return mismatch_error(inferred, expected)

        case (expected, requested, None) if expected == requested:
            source_suffix = expected

        case (expected, requested, None):
            assert expected is not None
            assert requested is not None
            return mismatch_error(requested, expected)

        case (expected, requested, inferred) if expected == requested == inferred:
            source_suffix = expected

        case (expected, requested, inferred) if expected != requested:
            assert expected is not None
            assert requested is not None
            return mismatch_error(requested, expected)

        case (expected, requested, inferred):
            assert expected is not None
            assert inferred is not None
            return mismatch_error(inferred, expected)

    normalized_source_suffix = f".{source_suffix}"

    source_config = config().find_source_for_extension(normalized_source_suffix)
    if source_config is None:
        return Err([NoSourceForArtifactExtension(artifact_id=full_id, path=input, extension=normalized_source_suffix)])

    render_context = RENDER_CONTEXT_VIEW
    test_artifact = source_config.construct_artifact_from_bytes(full_id, content_bytes, render_context).unwrap()
    validation_result = test_artifact.validate_artifact()

    validation_result.unwrap()
    world.update(full_id.artifact_id, content_bytes, normalized_source_suffix).unwrap()

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

    source_raw_artifact = source_world.fetch(source_id.artifact_id).unwrap()
    content_bytes = source_raw_artifact.get_bytes()
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

    render_context = RENDER_CONTEXT_VIEW
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
