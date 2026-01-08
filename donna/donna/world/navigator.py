
from donna.world.config import config
from donna.world.artifact_source import parse_artifact, ArtifactSource
from donna.world.primitives_register import register


def get_artifact(id: str) -> ArtifactSource:
    # Search from the outermost world to the innermost
    for world in reversed(config().worlds):
        if not world.has(id):
            continue

        content = world.extract(id)

        raw_artifact = parse_artifact(world.id, id, content)

        namespace = id.split("/")[0]

        kind = register().artifacts.get(namespace)

        if kind is None:
            raise NotImplementedError(f"Artifact kind for namespace `{namespace}` is not registered")

        artifact = kind.construct(raw_artifact)

        return artifact

    raise NotImplementedError(f"Artifact `{id}` does not exist in any configured world")


def list_artifacts(kind: str) -> list[ArtifactSource]:
    # TODO: optimize
    artifact_ids: set[str] = set()
    artifacts: list[ArtifactSource] = []

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
