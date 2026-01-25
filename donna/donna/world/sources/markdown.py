import uuid
from typing import Any, ClassVar, Literal, Protocol, cast

from donna.domain.ids import ArtifactLocalId, FullArtifactId, PythonImportPath
from donna.machine.artifacts import (
    Artifact,
    ArtifactSection,
    ArtifactSectionConfig,
    ArtifactSectionKind,
    ArtifactSectionMeta,
    resolve_section_kind,
)
from donna.world import markdown
from donna.world.sources.base import SourceConfig
from donna.world.templates import RenderMode, render, render_mode


class MarkdownSectionConstructor(Protocol):
    def markdown_construct_section(
        self,
        artifact_id: FullArtifactId,
        source: markdown.SectionSource,
        config: dict[str, Any],
        primary: bool = False,
    ) -> ArtifactSection:
        pass


class Config(SourceConfig):
    kind: Literal["markdown"] = "markdown"
    default_section_kind: PythonImportPath = PythonImportPath.parse("donna.lib.text")
    default_primary_section_id: ArtifactLocalId = ArtifactLocalId("primary")


class MarkdownSectionMixin:
    config_class: ClassVar[type[ArtifactSectionConfig]]

    def markdown_build_title(
        self,
        artifact_id: FullArtifactId,
        source: markdown.SectionSource,
        section_config: ArtifactSectionConfig,
        primary: bool = False,
    ) -> str:
        return source.title or ""

    def markdown_build_description(
        self,
        artifact_id: FullArtifactId,
        source: markdown.SectionSource,
        section_config: ArtifactSectionConfig,
        primary: bool = False,
    ) -> str:
        return source.as_original_markdown(with_title=False)

    def markdown_construct_meta(
        self,
        artifact_id: FullArtifactId,
        source: markdown.SectionSource,
        section_config: ArtifactSectionConfig,
        description: str,
        primary: bool = False,
    ) -> ArtifactSectionMeta:
        return ArtifactSectionMeta()

    def markdown_construct_section(  # noqa: CCR001
        self,
        artifact_id: FullArtifactId,
        source: markdown.SectionSource,
        config: dict[str, Any],
        primary: bool = False,
    ) -> ArtifactSection:
        section_config = self.config_class.parse_obj(config)

        title = self.markdown_build_title(
            artifact_id=artifact_id,
            source=source,
            section_config=section_config,
            primary=primary,
        )
        description = self.markdown_build_description(
            artifact_id=artifact_id,
            source=source,
            section_config=section_config,
            primary=primary,
        )
        meta = self.markdown_construct_meta(
            artifact_id=artifact_id,
            source=source,
            section_config=section_config,
            description=description,
            primary=primary,
        )

        return ArtifactSection(
            id=section_config.id,
            kind=section_config.kind,
            title=title,
            description=description,
            primary=primary,
            meta=meta,
        )


def parse_artifact_content(full_id: FullArtifactId, text: str) -> list[markdown.SectionSource]:
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

    return original_sections


def construct_artifact_from_bytes(full_id: FullArtifactId, content: bytes, config: Config) -> Artifact:
    return construct_artifact_from_markdown_source(full_id, content.decode("utf-8"), config)


def construct_artifact_from_markdown_source(full_id: FullArtifactId, content: str, config: Config) -> Artifact:
    original_sections = parse_artifact_content(full_id, content)

    head_config = dict(original_sections[0].merged_configs())
    head_kind_value = head_config["kind"]
    if isinstance(head_kind_value, PythonImportPath):
        head_kind = head_kind_value
    else:
        head_kind = PythonImportPath.parse(head_kind_value)

    if "id" not in head_config or head_config["id"] is None:
        head_config["id"] = config.default_primary_section_id

    primary_section_kind = resolve_section_kind(head_kind)
    _ensure_markdown_constructible(primary_section_kind, head_kind)
    markdown_primary_kind = cast(MarkdownSectionMixin, primary_section_kind)

    primary_section = markdown_primary_kind.markdown_construct_section(
        artifact_id=full_id,
        source=original_sections[0],
        config=head_config,
        primary=True,
    )

    sections = [primary_section]
    sections.extend(
        construct_sections_from_markdown(
            artifact_id=full_id,
            sections=original_sections[1:],
            default_section_kind=config.default_section_kind,
        )
    )

    return Artifact(
        id=full_id,
        sections=sections,
    )


def construct_sections_from_markdown(  # noqa: CCR001
    artifact_id: FullArtifactId,
    sections: list[markdown.SectionSource],
    default_section_kind: PythonImportPath,
    section_kind_overrides: dict[PythonImportPath, ArtifactSectionKind] | None = None,
) -> list[ArtifactSection]:
    constructed: list[ArtifactSection] = []

    for section in sections:
        data = dict(section.merged_configs())

        if "id" not in data or data["id"] is None:
            data["id"] = ArtifactLocalId("markdown" + uuid.uuid4().hex.replace("-", ""))

        if "kind" not in data:
            data["kind"] = default_section_kind

        kind_value = data["kind"]
        if isinstance(kind_value, str):
            section_kind_id = PythonImportPath.parse(kind_value)
        else:
            section_kind_id = kind_value

        section_kind = _resolve_section_kind(section_kind_id, section_kind_overrides)
        _ensure_markdown_constructible(section_kind, section_kind_id)
        markdown_section_kind = cast(MarkdownSectionMixin, section_kind)

        constructed.append(markdown_section_kind.markdown_construct_section(artifact_id, section, data, primary=False))

    return constructed


def _resolve_section_kind(
    section_kind_id: PythonImportPath,
    section_kind_overrides: dict[PythonImportPath, ArtifactSectionKind] | None = None,
) -> ArtifactSectionKind:
    if section_kind_overrides is not None and section_kind_id in section_kind_overrides:
        return section_kind_overrides[section_kind_id]

    return resolve_section_kind(section_kind_id)


def _ensure_markdown_constructible(
    section_kind: ArtifactSectionKind,
    section_kind_id: PythonImportPath | str | None = None,
) -> None:
    if isinstance(section_kind, MarkdownSectionMixin):
        return

    kind_label = f"'{section_kind_id}'" if section_kind_id is not None else repr(section_kind)
    raise NotImplementedError(f"Section kind {kind_label} cannot be constructed from markdown sources.")
