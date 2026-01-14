import pathlib

from donna.domain.ids import FullArtifactId, NamespaceId
from donna.machine.artifacts import Artifact
from donna.world import markdown
from donna.world.config import config
from donna.world.primitives_register import register
from donna.world.templates import RenderMode, render, render_mode


def parse_artifact(full_id: FullArtifactId, text: str) -> markdown.ArtifactSource:
    # Parsing an artifact two times is not ideal, but it is straightforward approach that works for now.
    # We should consider optimizing this in the future if performance or stability becomes an issue.
    # For now let's wait till we have more artifact analysis logic and till more use cases emerge.

    original_markdown_source = render(full_id, text)
    original_sections = markdown.parse(original_markdown_source)

    with render_mode(RenderMode.analysis):
        analyzed_markdown_source = render(full_id, text)
        analyzed_sections = markdown.parse(analyzed_markdown_source)

    if len(original_sections) != len(analyzed_sections):
        raise NotImplementedError("Artifact sections count mismatch between original and analyzed renderings")

    if not original_sections:
        raise NotImplementedError("Artifact must have at least one section")

    for original, analyzed in zip(original_sections, analyzed_sections):
        original.analysis_tokens.extend(analyzed.original_tokens)

    head = original_sections[0]
    tail = original_sections[1:]

    artifact = markdown.ArtifactSource(
        id=full_id,
        head=head,
        tail=tail,
    )

    return artifact


def fetch_artifact(full_id: FullArtifactId, output: pathlib.Path) -> None:
    world = config().get_world(full_id.world_id)

    if not world.has(full_id.namespace_id, full_id.artifact_id):
        raise NotImplementedError(f"Artifact `{full_id}` does not exist in world `{world.id}`")

    content = world.read(full_id.namespace_id, full_id.artifact_id)

    with output.open("wb") as f:
        f.write(content)


def update_artifact(full_id: FullArtifactId, input: pathlib.Path) -> None:
    world = config().get_world(full_id.world_id)

    if world.readonly:
        raise NotImplementedError(f"World `{world.id}` is read-only")

    content = input.read_text(encoding="utf-8")

    test_artifact = _construct_from_content(full_id, content)

    artifact_kind = register().artifacts.get(test_artifact.info.kind)

    is_valid, _cells = artifact_kind.validate_artifact(test_artifact)

    if not is_valid:
        raise NotImplementedError(f"Artifact `{full_id}` is not valid and cannot be updated")

    world.write(full_id.namespace_id, full_id.artifact_id, content)


def _construct_from_content(full_id: FullArtifactId, content: str) -> Artifact:
    raw_artifact = parse_artifact(full_id, content)

    kind = register().get_artifact_kind_by_namespace(full_id.namespace_id)

    if kind is None:
        raise NotImplementedError(f"Artifact kind for artifact `{full_id}` is not registered")

    return kind.construct(raw_artifact)


def load_artifact(full_id: FullArtifactId) -> Artifact:
    world = config().get_world(full_id.world_id)

    if not world.has(full_id.namespace_id, full_id.artifact_id):
        raise NotImplementedError(f"Artifact `{full_id}` does not exist in world `{world.id}`")

    content = world.read(full_id.namespace_id, full_id.artifact_id).decode("utf-8")

    return _construct_from_content(full_id, content)



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
