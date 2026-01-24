from typing import Any, Protocol

from donna.domain.ids import FullArtifactId, FullArtifactLocalId
from donna.machine.artifacts import (
    Artifact,
    ArtifactContent,
    ArtifactSection,
    ArtifactSectionKind,
    ArtifactSectionKindMeta,
    SectionContent,
    resolve,
)
from donna.world import markdown
from donna.world.templates import RenderMode, render, render_mode


class MarkdownSectionConstructor(Protocol):
    def from_markdown_section(
        self,
        artifact_id: FullArtifactId,
        source: markdown.SectionSource,
        config: dict[str, Any],
        primary: bool = False,
    ) -> ArtifactSection:
        pass


def parse_artifact_content(full_id: FullArtifactId, text: str) -> tuple[ArtifactContent, list[markdown.SectionSource]]:
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

    content = ArtifactContent(
        id=full_id,
        head=_section_content_from_source(head_source),
        tail=[_section_content_from_source(section) for section in tail_sources],
    )
    return content, original_sections


def construct_artifact_from_markdown_source(full_id: FullArtifactId, content: str) -> Artifact:
    raw_artifact, original_sections = parse_artifact_content(full_id, content)

    head_kind = FullArtifactLocalId.parse(raw_artifact.head.config["kind"])

    section = resolve(head_kind)

    if not isinstance(section.meta, ArtifactSectionKindMeta):
        raise NotImplementedError(f"Primary section kind '{head_kind}' is not available")

    primary_section_kind = section.meta.section_kind

    primary_section = primary_section_kind.from_markdown_section(
        artifact_id=full_id,
        source=original_sections[0],
        config=raw_artifact.head.config,
        primary=True,
    )

    sections = [primary_section]
    sections.extend(
        construct_sections_from_markdown(
            artifact_id=full_id,
            sections=original_sections[1:],
            default_section_kind=primary_section_kind.default_section_kind,
        )
    )

    return Artifact(
        id=full_id,
        sections=sections,
    )


def construct_sections_from_markdown(  # noqa: CCR001
    artifact_id: FullArtifactId,
    sections: list[markdown.SectionSource],
    default_section_kind: FullArtifactLocalId,
    section_kind_overrides: dict[FullArtifactLocalId, ArtifactSectionKind] | None = None,
) -> list[ArtifactSection]:
    constructed: list[ArtifactSection] = []

    for section in sections:
        data = dict(section.merged_configs())

        if "kind" not in data:
            data["kind"] = default_section_kind

        kind_value = data["kind"]
        if isinstance(kind_value, str):
            section_kind_id = FullArtifactLocalId.parse(kind_value)
        else:
            section_kind_id = kind_value

        section_kind = _resolve_section_kind(section_kind_id, section_kind_overrides)

        constructed.append(section_kind.from_markdown_section(artifact_id, section, data, primary=False))

    return constructed


def _resolve_section_kind(
    section_kind_id: FullArtifactLocalId,
    section_kind_overrides: dict[FullArtifactLocalId, ArtifactSectionKind] | None = None,
) -> ArtifactSectionKind:
    if section_kind_overrides is not None and section_kind_id in section_kind_overrides:
        return section_kind_overrides[section_kind_id]

    resolved_section = resolve(section_kind_id)
    if not isinstance(resolved_section.meta, ArtifactSectionKindMeta):
        raise NotImplementedError(f"Section kind '{section_kind_id}' is not available")
    return resolved_section.meta.section_kind


def _section_content_from_source(section: markdown.SectionSource) -> SectionContent:
    title = section.title or ""

    return SectionContent(
        title=title,
        description=section.as_original_markdown(with_title=False),
        analysis=section.as_analysis_markdown(with_title=True),
        config=section.merged_configs(),
    )
