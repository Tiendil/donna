import uuid
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Protocol, cast

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import ArtifactSectionId, FullArtifactId, PythonImportPath
from donna.machine.artifacts import Artifact, ArtifactSection, ArtifactSectionConfig, ArtifactSectionMeta
from donna.machine.primitives import Primitive, resolve_primitive
from donna.world import errors as world_errors
from donna.world import markdown
from donna.world.sources.base import SourceConfig, SourceConstructor
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
    supported_extensions: list[str] = [".md", ".markdown"]
    default_section_kind: PythonImportPath = PythonImportPath("donna.lib.text")
    default_primary_section_id: ArtifactSectionId = ArtifactSectionId("primary")

    def construct_artifact_from_bytes(self, full_id: FullArtifactId, content: bytes) -> Result[Artifact, ErrorsList]:
        return construct_artifact_from_bytes(full_id, content, self)


class MarkdownSourceConstructor(SourceConstructor):
    def construct_source(self, config: "SourceConfigModel") -> Config:
        data = config.model_dump()
        data.pop("kind", None)
        return Config.model_validate(data)


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
            artifact_id=artifact_id,
            kind=section_config.kind,
            title=title,
            description=description,
            primary=primary,
            meta=meta,
        )


@unwrap_to_error
def parse_artifact_content(full_id: FullArtifactId, text: str) -> Result[list[markdown.SectionSource], ErrorsList]:
    # Parsing an artifact two times is not ideal, but it is straightforward approach that works for now.
    # We should consider optimizing this in the future if performance or stability becomes an issue.
    # For now let's wait till we have more artifact analysis logic and till more use cases emerge.

    original_markdown_source = render(full_id, text)
    original_sections = markdown.parse(original_markdown_source, artifact_id=full_id).unwrap()

    with render_mode(RenderMode.analysis):
        analyzed_markdown_source = render(full_id, text)
        analyzed_sections = markdown.parse(analyzed_markdown_source, artifact_id=full_id).unwrap()

    if len(original_sections) != len(analyzed_sections):
        raise world_errors.MarkdownSectionsCountMismatch(
            artifact_id=full_id,
            original_count=len(original_sections),
            analyzed_count=len(analyzed_sections),
        )

    if not original_sections:
        # return Envrironment errors
        return Err([world_errors.MarkdownArtifactWithoutSections(artifact_id=full_id)])

    for original, analyzed in zip(original_sections, analyzed_sections):
        original.analysis_tokens.extend(analyzed.original_tokens)

    return Ok(original_sections)


def construct_artifact_from_bytes(
    full_id: FullArtifactId, content: bytes, config: Config
) -> Result[Artifact, ErrorsList]:
    return construct_artifact_from_markdown_source(full_id, content.decode("utf-8"), config)


@unwrap_to_error
def construct_artifact_from_markdown_source(  # noqa: CCR001
    full_id: FullArtifactId, content: str, config: Config
) -> Result[Artifact, ErrorsList]:
    original_sections = parse_artifact_content(full_id, content).unwrap()
    head_config = dict(original_sections[0].merged_configs().unwrap())
    head_kind_value = head_config["kind"]
    if isinstance(head_kind_value, PythonImportPath):
        head_kind = head_kind_value
    else:
        head_kind = PythonImportPath.parse(head_kind_value).unwrap()

    if "id" not in head_config or head_config["id"] is None:
        head_config["id"] = config.default_primary_section_id

    primary_primitive = resolve_primitive(head_kind).unwrap()
    _ensure_markdown_constructible(primary_primitive, head_kind).unwrap()
    markdown_primary_primitive = cast(MarkdownSectionMixin, primary_primitive)

    primary_section = markdown_primary_primitive.markdown_construct_section(
        artifact_id=full_id,
        source=original_sections[0],
        config=head_config,
        primary=True,
    )

    sections = [primary_section]
    sections = construct_sections_from_markdown(
        artifact_id=full_id,
        sections=original_sections[1:],
        default_section_kind=config.default_section_kind,
    ).unwrap()
    sections = [primary_section, *sections]
    return Ok(Artifact(id=full_id, sections=sections))


@unwrap_to_error
def construct_sections_from_markdown(  # noqa: CCR001
    artifact_id: FullArtifactId,
    sections: list[markdown.SectionSource],
    default_section_kind: PythonImportPath,
    primitive_overrides: dict[PythonImportPath, Primitive] | None = None,
) -> Result[list[ArtifactSection], ErrorsList]:
    constructed: list[ArtifactSection] = []

    for section in sections:
        data = dict(section.merged_configs().unwrap())

        if "id" not in data or data["id"] is None:
            data["id"] = ArtifactSectionId("markdown" + uuid.uuid4().hex.replace("-", ""))

        if "kind" not in data:
            data["kind"] = default_section_kind

        kind_value = data["kind"]
        if isinstance(kind_value, str):
            primitive_id = PythonImportPath.parse(kind_value).unwrap()
        else:
            primitive_id = kind_value

        primitive = _resolve_primitive(primitive_id, primitive_overrides).unwrap()
        _ensure_markdown_constructible(primitive, primitive_id).unwrap()
        markdown_primitive = cast(MarkdownSectionMixin, primitive)

        constructed.append(markdown_primitive.markdown_construct_section(artifact_id, section, data, primary=False))

    return Ok(constructed)


def _resolve_primitive(
    primitive_id: PythonImportPath,
    primitive_overrides: dict[PythonImportPath, Primitive] | None = None,
) -> Result[Primitive, ErrorsList]:
    if primitive_overrides is not None and primitive_id in primitive_overrides:
        return Ok(primitive_overrides[primitive_id])

    return resolve_primitive(primitive_id)


def _ensure_markdown_constructible(
    primitive: Primitive,
    primitive_id: PythonImportPath | str | None = None,
) -> Result[None, ErrorsList]:
    if isinstance(primitive, MarkdownSectionMixin):
        return Ok(None)

    kind_label = f"'{primitive_id}'" if primitive_id is not None else repr(primitive)

    return Err([world_errors.PrimitiveDoesNotSupportMarkdown(primitive_id=kind_label)])


if TYPE_CHECKING:
    from donna.world.config import SourceConfig as SourceConfigModel
