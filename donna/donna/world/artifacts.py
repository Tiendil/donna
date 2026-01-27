import pathlib

from donna.domain.ids import FullArtifactId, FullArtifactIdPattern
from donna.machine.artifacts import Artifact
from donna.world.config import config


def artifact_file_extension(full_id: FullArtifactId) -> str:
    world = config().get_world(full_id.world_id)
    extension = world.file_extension_for(full_id.artifact_id)

    if extension is None:
        raise NotImplementedError(f"Artifact `{full_id}` does not exist in world `{world.id}`")

    return extension.lstrip(".")


def fetch_artifact(full_id: FullArtifactId, output: pathlib.Path) -> None:
    world = config().get_world(full_id.world_id)

    if not world.has(full_id.artifact_id):
        raise NotImplementedError(f"Artifact `{full_id}` does not exist in world `{world.id}`")

    content = world.fetch_source(full_id.artifact_id)

    with output.open("wb") as f:
        f.write(content)


def update_artifact(full_id: FullArtifactId, input: pathlib.Path) -> None:
    world = config().get_world(full_id.world_id)

    if world.readonly:
        raise NotImplementedError(f"World `{world.id}` is read-only")

    source_suffix = input.suffix.lower()
    content_bytes = input.read_bytes()

    if not source_suffix:
        raise NotImplementedError(f"Unsupported artifact source extension '{input.suffix}'")

    source_config = config().find_source_for_extension(source_suffix)
    if source_config is None:
        raise NotImplementedError(f"Unsupported artifact source extension '{input.suffix}'")

    test_artifact = source_config.construct_artifact_from_bytes(full_id, content_bytes)

    errors = test_artifact.validate_artifact()

    # TODO: this is bad solution, we must return a list of errors instead
    if errors:
        raise NotImplementedError(f"Artifact `{full_id}` is not valid and cannot be updated")

    world.update(full_id.artifact_id, content_bytes, source_suffix)


def load_artifact(full_id: FullArtifactId) -> Artifact:
    world = config().get_world(full_id.world_id)

    if not world.has(full_id.artifact_id):
        raise NotImplementedError(f"Artifact `{full_id}` does not exist in world `{world.id}`")

    return world.fetch(full_id.artifact_id)


def list_artifacts(pattern: FullArtifactIdPattern) -> list[Artifact]:
    artifacts: list[Artifact] = []

    for world in reversed(config().worlds_instances):
        for artifact_id in world.list_artifacts(pattern):
            full_id = FullArtifactId((world.id, artifact_id))
            artifact = load_artifact(full_id)
            artifacts.append(artifact)

    return artifacts
