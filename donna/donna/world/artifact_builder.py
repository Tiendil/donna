from donna.domain.ids import FullArtifactId
from donna.machine.artifacts import Artifact
from donna.world import markdown
from donna.world.primitives_register import register
from donna.world.templates import RenderMode, render, render_mode


def parse_artifact_source(full_id: FullArtifactId, text: str) -> markdown.ArtifactSource:
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


def construct_artifact_from_content(full_id: FullArtifactId, content: str) -> Artifact:
    raw_artifact = parse_artifact_source(full_id, content)

    kind = register().get_artifact_kind_by_namespace(full_id.namespace_id)

    if kind is None:
        raise NotImplementedError(f"Artifact kind for artifact `{full_id}` is not registered")

    return kind.construct_artifact(raw_artifact)
