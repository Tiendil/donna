import pathlib

from donna.domain.ids import FullArtifactId, NamespaceId
from donna.machine.artifacts import Artifact, resolve_artifact_kind
from donna.world.artifact_builder import construct_artifact_from_content
from donna.world.config import config
from donna.world.primitives_register import register


def fetch_artifact(full_id: FullArtifactId, output: pathlib.Path) -> None:
    world = config().get_world(full_id.world_id)

    if not world.has(full_id.namespace_id, full_id.artifact_id):
        raise NotImplementedError(f"Artifact `{full_id}` does not exist in world `{world.id}`")

    content = world.fetch_source(full_id.namespace_id, full_id.artifact_id)

    with output.open("wb") as f:
        f.write(content)


def update_artifact(full_id: FullArtifactId, input: pathlib.Path) -> None:
    world = config().get_world(full_id.world_id)

    if world.readonly:
        raise NotImplementedError(f"World `{world.id}` is read-only")

    content = input.read_text(encoding="utf-8")

    test_artifact = construct_artifact_from_content(full_id, content)

    assert test_artifact.kind is not None

    artifact_kind = resolve_artifact_kind(test_artifact.kind)

    is_valid, _cells = artifact_kind.validate_artifact(test_artifact)

    if not is_valid:
        raise NotImplementedError(f"Artifact `{full_id}` is not valid and cannot be updated")

    world.update(full_id.namespace_id, full_id.artifact_id, content.encode("utf-8"))


def load_artifact(full_id: FullArtifactId) -> Artifact:
    world = config().get_world(full_id.world_id)

    if not world.has(full_id.namespace_id, full_id.artifact_id):
        raise NotImplementedError(f"Artifact `{full_id}` does not exist in world `{world.id}`")

    return world.fetch(full_id.namespace_id, full_id.artifact_id)


def list_artifacts(namespace_id: NamespaceId) -> list[Artifact]:
    artifacts: list[Artifact] = []

    for world in reversed(config().worlds):
        for artifact_id in world.list_artifacts(namespace_id):
            full_id = FullArtifactId((world.id, namespace_id, artifact_id))
            artifact = load_artifact(full_id)
            artifacts.append(artifact)

    return artifacts


def load_code() -> None:
    # IMPORTANT:
    # 1. Donna imports everything: this is the only navigation code that doesn't redefine loaded artifacts
    # 2. Donna imports in straight order: from innermost to outermost world
    for world in config().worlds:
        for module in world.get_modules():
            register().register_module(module)


# TODO: do we need smart initialization here?
load_code()
