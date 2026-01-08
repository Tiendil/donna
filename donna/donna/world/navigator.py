
from donna.world.config import config
from donna.world.artifact_source import parse_artifact, ArtifactSource
from donna.world.primitives_register import register


def get(id: str) -> ArtifactSource:
    cfg = config()

    # Search from the outermost world to the innermost
    for world in reversed(cfg.worlds):
        if not world.has(id):
            continue

        content = world.extract(id)

        raw_artifact = parse_artifact(world.id, id, content)

        kind = id.split("/")[0]

        kind = register().artifacts.get(kind)

        if kind is None:
            raise NotImplementedError(f"Artifact kind `{kind}` is not registered")

        artifact = kind.construct(raw_artifact)

        return artifact

    raise NotImplementedError(f"Artifact `{id}` does not exist in any configured world")


def load_code() -> None:

    cfg = config()

    # IMPORTANT:
    # 1. Donna imports everything: this is the only navigation code that doesn't redefine loaded artifacts
    # 2. Donna imports in straight order: from innermost to outermost world
    for world in cfg.worlds:
        for module in world.get_modules():
            register().register_module(module)


# TODO: do we need smart initialization here?
load_code()
