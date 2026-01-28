import pathlib

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import FullArtifactId, FullArtifactIdPattern, WorldId
from donna.machine.artifacts import Artifact
from donna.world import errors
from donna.world.config import config


class ArtifactUpdateError(errors.WorldError):
    cell_kind: str = "artifact_update_error"
    artifact_id: FullArtifactId
    path: pathlib.Path

    def content_intro(self) -> str:
        return f"Error updating artifact '{self.artifact_id}' from the path '{self.path}'"


class CanNotUpdateReadonlyWorld(ArtifactUpdateError):
    code: str = "donna.world.cannot_update_readonly_world"
    message: str = "Cannot upload artifact to the read-only world `{error.world_id}`"
    world_id: WorldId


class InputPathHasNoExtension(ArtifactUpdateError):
    code: str = "donna.world.input_path_has_no_extension"
    message: str = "Input path has no extension to determine artifact source type"


class NoSourceForArtifactExtension(ArtifactUpdateError):
    code: str = "donna.world.no_source_for_artifact_extension"
    message: str = "No source found for artifact extension of input path"


def artifact_file_extension(full_id: FullArtifactId) -> Result[str, ErrorsList]:
    world_result = config().get_world(full_id.world_id)
    if world_result.is_err():
        return Err(world_result.unwrap_err())

    world = world_result.unwrap()
    extension_result = world.file_extension_for(full_id.artifact_id)
    if extension_result.is_err():
        return Err(extension_result.unwrap_err())

    return Ok(extension_result.unwrap().lstrip("."))


def fetch_artifact(full_id: FullArtifactId, output: pathlib.Path) -> Result[None, ErrorsList]:
    world_result = config().get_world(full_id.world_id)
    if world_result.is_err():
        return Err(world_result.unwrap_err())

    world = world_result.unwrap()
    content_result = world.fetch_source(full_id.artifact_id)
    if content_result.is_err():
        return Err(content_result.unwrap_err())

    content = content_result.unwrap()

    with output.open("wb") as f:
        f.write(content)

    return Ok(None)


def update_artifact(full_id: FullArtifactId, input: pathlib.Path) -> Result[None, ErrorsList]:
    world_result = config().get_world(full_id.world_id)
    if world_result.is_err():
        return Err(world_result.unwrap_err())

    world = world_result.unwrap()

    if world.readonly:
        return Err([CanNotUpdateReadonlyWorld(artifact_id=full_id, path=input, world_id=world.id)])

    source_suffix = input.suffix.lower()
    content_bytes = input.read_bytes()

    if not source_suffix:
        return Err([InputPathHasNoExtension(artifact_id=full_id, path=input)])

    source_config = config().find_source_for_extension(source_suffix)
    if source_config is None:
        return Err([NoSourceForArtifactExtension(artifact_id=full_id, path=input)])

    test_artifact_result = source_config.construct_artifact_from_bytes(full_id, content_bytes)
    if test_artifact_result.is_err():
        return Err(test_artifact_result.unwrap_err())

    test_artifact = test_artifact_result.unwrap()
    validation_result = test_artifact.validate_artifact()

    if validation_result.is_err():
        return Err(validation_result.unwrap_err())

    update_result = world.update(full_id.artifact_id, content_bytes, source_suffix)
    if update_result.is_err():
        return Err(update_result.unwrap_err())

    return Ok(None)


def load_artifact(full_id: FullArtifactId) -> Result[Artifact, ErrorsList]:
    world_result = config().get_world(full_id.world_id)
    if world_result.is_err():
        return Err(world_result.unwrap_err())

    world = world_result.unwrap()

    artifact_result = world.fetch(full_id.artifact_id)
    if artifact_result.is_err():
        return Err(artifact_result.unwrap_err())

    return Ok(artifact_result.unwrap())


def list_artifacts(pattern: FullArtifactIdPattern) -> Result[list[Artifact], ErrorsList]:
    artifacts: list[Artifact] = []
    errors: ErrorsList = []

    for world in reversed(config().worlds_instances):
        for artifact_id in world.list_artifacts(pattern):
            full_id = FullArtifactId((world.id, artifact_id))
            artifact_result = load_artifact(full_id)
            if artifact_result.is_err():
                errors.extend(artifact_result.unwrap_err())
                continue
            artifacts.append(artifact_result.unwrap())

    if errors:
        return Err(errors)

    return Ok(artifacts)
