import pathlib

from donna.domain.ids import ArtifactId, FullArtifactId
from donna.machine.artifacts import Artifact, ArtifactKindSectionMeta, resolve
from donna.world.config import config
from donna.world.sources.markdown import construct_artifact_from_markdown_source


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

    content = input.read_text(encoding="utf-8")

    test_artifact = construct_artifact_from_markdown_source(full_id, content)

    assert test_artifact.kind is not None

    section = resolve(test_artifact.kind)
    if not isinstance(section.meta, ArtifactKindSectionMeta):
        raise NotImplementedError(f"Artifact kind '{test_artifact.kind}' is not available")
    artifact_kind = section.meta.artifact_kind

    is_valid, _cells = artifact_kind.validate_artifact(test_artifact)

    if not is_valid:
        raise NotImplementedError(f"Artifact `{full_id}` is not valid and cannot be updated")

    world.update(full_id.artifact_id, content.encode("utf-8"))


def load_artifact(full_id: FullArtifactId) -> Artifact:
    world = config().get_world(full_id.world_id)

    if not world.has(full_id.artifact_id):
        raise NotImplementedError(f"Artifact `{full_id}` does not exist in world `{world.id}`")

    return world.fetch(full_id.artifact_id)


def list_artifacts(artifact_prefix: ArtifactId) -> list[Artifact]:
    artifacts: list[Artifact] = []

    for world in reversed(config().worlds):
        for artifact_id in world.list_artifacts(artifact_prefix):
            full_id = FullArtifactId((world.id, artifact_id))
            artifact = load_artifact(full_id)
            artifacts.append(artifact)

    return artifacts
