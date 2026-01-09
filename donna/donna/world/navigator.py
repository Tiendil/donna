from donna.machine.artifacts import Artifact
from donna.domain.ids import FullArtifactId
from donna.world.artifacts import parse_artifact
from donna.world.config import config
from donna.world.primitives_register import register


def get_artifact(full_id: FullArtifactId) -> Artifact:

    world = config().get_world(id.world_id)

    if not world.has(full_id.namespace_id, full_id.artifact_id):
        raise NotImplementedError(f"Artifact `{full_id}` does not exist in world `{world.id}`")

    content = world.extract(full_id.namespace_id, full_id.artifact_id)

    raw_artifact = parse_artifact(full_id, content)

    kind = register().get_artifact_kind_by_namespace(full_id.namespace_id)

    if kind is None:
        raise NotImplementedError(f"Artifact kind for artifact `{full_id}` is not registered")

    return kind.construct(raw_artifact)


def list_artifacts(kind: str) -> list[Artifact]:
    # TODO: optimize
    artifact_ids: set[str] = set()
    artifacts: list[Artifact] = []

    for world in reversed(config().worlds):
        artifact_ids.update(world.list_artifacts(kind))

    for artifact_id in artifact_ids:
        artifact = get_artifact(artifact_id)
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
