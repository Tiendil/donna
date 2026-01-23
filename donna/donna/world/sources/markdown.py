from donna.domain.ids import FullArtifactId
from donna.machine.artifacts import (
    Artifact,
    ArtifactConfig,
    ArtifactContent,
    ArtifactKindSectionMeta,
    SectionContent,
    resolve,
)
from donna.world import markdown
from donna.world.templates import RenderMode, render, render_mode


def parse_artifact_content(full_id: FullArtifactId, text: str) -> ArtifactContent:
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

    head_source = original_sections[0]
    tail_sources = original_sections[1:]

    return ArtifactContent(
        id=full_id,
        head=_section_content_from_source(head_source),
        tail=[_section_content_from_source(section) for section in tail_sources],
    )


def construct_artifact_from_markdown_source(full_id: FullArtifactId, content: str) -> Artifact:
    raw_artifact = parse_artifact_content(full_id, content)

    config = ArtifactConfig.parse_obj(raw_artifact.head.config)
    section = resolve(config.kind)
    if not isinstance(section.meta, ArtifactKindSectionMeta):
        raise NotImplementedError(f"Artifact kind '{config.kind}' is not available")
    kind = section.meta.artifact_kind

    return kind.construct_artifact(raw_artifact)


def _section_content_from_source(section: markdown.SectionSource) -> SectionContent:
    title = section.title or ""

    return SectionContent(
        title=title,
        description=section.as_original_markdown(with_title=False),
        analysis=section.as_analysis_markdown(with_title=True),
        config=section.merged_configs(),
    )
