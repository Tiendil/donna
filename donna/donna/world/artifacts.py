from donna.domain.ids import FullArtifactId
from donna.world import markdown
from donna.world.templates import render, RenderMode, render_mode


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
