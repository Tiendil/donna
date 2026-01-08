
from donna.world.config import config
from donna.world.artifact_source import parse_artifact, ArtifactSource


def get(id: str) -> ArtifactSource:
    cfg = config()

    for world in cfg.worlds:
        if not world.has(id):
            continue

        content = world.get(id)

        raw_artifact = parse_artifact(world.id, id, content)

        return raw_artifact

    raise NotImplementedError(f"Artifact `{id}` does not exist in any configured world")
