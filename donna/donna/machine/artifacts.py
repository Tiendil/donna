import enum
import inspect
import types
import uuid
from typing import TYPE_CHECKING, Any, Iterable

from markdown_it import MarkdownIt

from donna.core.entities import BaseEntity
from donna.domain.ids import ArtifactLocalId, FullArtifactId, FullArtifactLocalId
from donna.machine.cells import Cell
from donna.machine.tasks import Task, WorkUnit
from donna.world.markdown import ArtifactSource, CodeSource, SectionLevel, SectionSource

if TYPE_CHECKING:
    from donna.machine.changes import Change


class ArtifactKind(BaseEntity):
    default_section_kind: FullArtifactLocalId = FullArtifactLocalId.parse("donna.operations:text")

    def construct_section(
        self,
        artifact_id: FullArtifactId,
        raw_section: SectionSource,
        section_kind_overrides: dict[FullArtifactLocalId, "ArtifactSectionKind"] | None = None,
    ) -> "ArtifactSection":
        data = raw_section.merged_configs()

        if "kind" not in data:
            data["kind"] = self.default_section_kind

        kind_value = data["kind"]
        if isinstance(kind_value, str):
            section_kind_id = FullArtifactLocalId.parse(kind_value)
        else:
            section_kind_id = kind_value

        if "kind" not in raw_section.merged_configs():
            raw_section = raw_section.model_copy(
                update={
                    "configs": raw_section.configs
                    + [
                        CodeSource(
                            format="toml",
                            properties={"donna": True},
                            content=f'kind = "{section_kind_id}"',
                        )
                    ]
                }
            )

        section_kind = None
        if section_kind_overrides is not None:
            section_kind = section_kind_overrides.get(section_kind_id)

        if section_kind is None:
            section_kind = resolve_section_kind(section_kind_id)

        section = section_kind.construct_section(artifact_id, raw_section)

        return section

    def construct_artifact(self, source: ArtifactSource) -> "Artifact":
        raise NotImplementedError("You must implement this method in subclasses")

    def validate_artifact(self, artifact: "Artifact") -> tuple[bool, list[Cell]]:
        return True, [
            Cell.build_meta(
                kind="artifact_kind_validation",
                id=str(artifact.id),
                status="success",
            )
        ]


class ArtifactSectionConfig(BaseEntity):
    id: ArtifactLocalId
    kind: FullArtifactLocalId


class ArtifactConfig(BaseEntity):
    kind: FullArtifactLocalId


class ArtifactSectionMeta(BaseEntity):
    def cells_meta(self) -> dict[str, Any]:
        return {}


class ArtifactSection(BaseEntity):
    # some section may have no id and kind — it is ok for simple text sections
    id: FullArtifactLocalId | None
    kind: FullArtifactLocalId | None
    title: str
    description: str

    meta: ArtifactSectionMeta
    entity: BaseEntity | None = None

    def cells(self) -> list[Cell]:
        return [
            Cell.build_meta(
                kind="artifact_section_meta",
                section_id=str(self.id) if self.id else None,
                section_kind=str(self.kind) if self.kind else None,
                section_title=self.title,
                section_description=self.description,
                **self.meta.cells_meta(),
            )
        ]

    def markdown_blocks(self) -> list[str]:
        return [f"## {self.title}", self.description]


class ArtifactMeta(BaseEntity):

    def cells_meta(self) -> dict[str, Any]:
        return {}


class Artifact(BaseEntity):
    id: FullArtifactId
    kind: FullArtifactLocalId
    title: str
    description: str

    meta: ArtifactMeta
    sections: list[ArtifactSection]

    # TODO: should we attach section cells here as well?
    def cells(self) -> list[Cell]:
        cells = [
            Cell.build_meta(
                kind="artifact_meta",
                artifact_id=str(self.id),
                artifact_kind=str(self.kind),
                artifact_title=self.title,
                artifact_description=self.description,
                **self.meta.cells_meta(),
            )
        ]

        markdown = "\n".join(self.markdown_blocks())

        cells.append(Cell.build_markdown(kind="artifact_markdown", content=markdown, artifact_id=str(self.id)))

        return cells

    def get_section(self, section_id: FullArtifactLocalId) -> ArtifactSection | None:
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

    def markdown_blocks(self) -> list[str]:
        blocks = [f"# {self.title}", self.description]

        for section in self.sections:
            blocks.extend(section.markdown_blocks())

        return blocks


class ArtifactSectionKind(BaseEntity):
    def execute_section(self, task: Task, unit: WorkUnit, section: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("You MUST implement this method.")

    def construct_section(self, artifact_id: FullArtifactId, raw_section: SectionSource) -> ArtifactSection:
        raise NotImplementedError("You MUST implement this method.")


class TextConfig(ArtifactSectionConfig):
    pass


class PythonModuleSectionConfig(ArtifactSectionConfig):
    pass


class ArtifactSectionTextKind(ArtifactSectionKind):

    def execute_section(self, task: Task, unit: WorkUnit, operation: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("Text sections cannot be executed.")

    def construct_section(self, artifact_id: FullArtifactId, raw_section: SectionSource) -> ArtifactSection:
        data = raw_section.merged_configs()

        if "id" not in data:
            # TODO: we should replace this hack with a proper ID generator
            #       to keep that id stable between runs
            #       options:
            #       - a hash of the content
            #       - a sequential ID generator per artifact
            data["id"] = "text" + uuid.uuid4().hex.replace("-", "")

        config = TextConfig.parse_obj(data)

        title = raw_section.title or ""

        return ArtifactSection(
            id=artifact_id.to_full_local(config.id),
            kind=config.kind,
            title=title,
            description=raw_section.as_original_markdown(with_title=False),
            meta=ArtifactSectionMeta(),
        )


class PythonModuleSectionMeta(ArtifactSectionMeta):
    attribute_value: Any

    model_config = BaseEntity.model_config | {"arbitrary_types_allowed": True}

    def cells_meta(self) -> dict[str, Any]:
        return {"attribute_value": repr(self.attribute_value)}


class PythonModuleSectionKind(ArtifactSectionKind):

    def execute_section(self, task: Task, unit: WorkUnit, operation: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("Python module sections cannot be executed.")

    def construct_section(self, artifact_id: FullArtifactId, raw_section: SectionSource) -> ArtifactSection:
        data = raw_section.merged_configs()
        config_data = {
            "id": data.get("id"),
            "kind": data.get("kind"),
        }
        config = PythonModuleSectionConfig.parse_obj(config_data)

        title = raw_section.title or ""

        return ArtifactSection(
            id=artifact_id.to_full_local(config.id),
            kind=config.kind,
            title=title,
            description=raw_section.as_original_markdown(with_title=False),
            meta=ArtifactSectionMeta(),
        )


class PythonArtifact(ArtifactKind):

    def construct_artifact(self, source: ArtifactSource) -> "Artifact":
        raise NotImplementedError("Python artifacts are constructed from modules, not markdown sources.")

    def construct_module_artifact(  # noqa: CCR001
        self,
        module: types.ModuleType,
        artifact_id: FullArtifactId,
        kind_id: FullArtifactLocalId,
    ) -> "Artifact":
        artifact_constructor: ArtifactConstructor | None = None

        for value in module.__dict__.values():
            if isinstance(value, ArtifactConstructor):
                if artifact_constructor is not None:
                    raise NotImplementedError("Artifact module must define only one ArtifactConstructor.")

                artifact_constructor = value

        if artifact_constructor is None:
            title = module.__name__
            description = inspect.getdoc(module) or ""
            artifact_kind_id = kind_id
        else:
            head_section = artifact_constructor.construct_head()
            title = head_section.title or module.__name__
            description = head_section.as_original_markdown(with_title=False)
            artifact_kind_id = ArtifactConfig.parse_obj(head_section.merged_configs()).kind

            if artifact_kind_id != kind_id:
                raise NotImplementedError(
                    f"Artifact kind mismatch: constructor uses '{artifact_kind_id}', but expected '{kind_id}'."
                )

        sections: list[ArtifactSection] = []

        constructors: list[SectionConstructor] = []
        section_kind_overrides: dict[FullArtifactLocalId, ArtifactSectionKind] = {}

        for name, value in sorted(module.__dict__.items()):
            if not name.isidentifier():
                continue

            if name.startswith("_"):
                continue

            if isinstance(value, SectionConstructor):
                constructors.append(value)

                if value.entity is not None and isinstance(value.entity, ArtifactSectionKind):
                    section_id = artifact_id.to_full_local(value.config.id)
                    section_kind_overrides[section_id] = value.entity

        for constructor in constructors:
            section = constructor.build_section(
                artifact_kind=self,
                artifact_id=artifact_id,
                section_kind_overrides=section_kind_overrides,
            )
            sections.append(section)

        return Artifact(
            id=artifact_id,
            kind=artifact_kind_id,
            title=title,
            description=description,
            meta=ArtifactMeta(),
            sections=sections,
        )


def resolve_section_kind(section_kind_id: FullArtifactLocalId) -> ArtifactSectionKind:
    from donna.world import artifacts as world_artifacts

    artifact = world_artifacts.load_artifact(section_kind_id.full_artifact_id)
    section = artifact.get_section(section_kind_id)

    if section is None or section.entity is None or not isinstance(section.entity, ArtifactSectionKind):
        raise NotImplementedError(f"Section kind '{section_kind_id}' is not available")

    return section.entity


def resolve_artifact_kind(artifact_kind_id: FullArtifactLocalId) -> ArtifactKind:
    from donna.world import artifacts as world_artifacts

    artifact = world_artifacts.load_artifact(artifact_kind_id.full_artifact_id)
    section = artifact.get_section(artifact_kind_id)

    if section is None or section.entity is None or not isinstance(section.entity, ArtifactKind):
        raise NotImplementedError(f"Artifact kind '{artifact_kind_id}' is not available")

    return section.entity


def _markdown_tokens(text: str) -> list[Any]:
    if not text:
        return []

    md = MarkdownIt("commonmark")
    return md.parse(text)


def _serialize_toml_value(value: Any) -> str:  # noqa: CCR001
    if isinstance(value, enum.Enum):
        value = value.value

    if isinstance(value, (ArtifactLocalId, FullArtifactId, FullArtifactLocalId)):
        value = str(value)

    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, (list, tuple, set)):
        return "[" + ", ".join(_serialize_toml_value(item) for item in value) + "]"

    raise NotImplementedError(f"Unsupported TOML value: {value!r}")


class SectionConstructor(BaseEntity):
    title: str
    description: str
    config: ArtifactSectionConfig
    entity: BaseEntity | None = None

    def build_section(  # noqa: CCR001
        self,
        artifact_kind: ArtifactKind,
        artifact_id: FullArtifactId,
        section_kind_overrides: dict[FullArtifactLocalId, ArtifactSectionKind] | None = None,
    ) -> ArtifactSection:
        config_data = self.config.model_dump(mode="json")

        config_lines = []
        for key in sorted(config_data.keys()):
            config_lines.append(f"{key} = {_serialize_toml_value(config_data[key])}")

        raw_section = SectionSource(
            level=SectionLevel.h2,
            title=self.title,
            configs=[
                CodeSource(
                    format="toml",
                    properties={"donna": True},
                    content="\n".join(config_lines),
                )
            ],
            original_tokens=_markdown_tokens(self.description),
            analysis_tokens=_markdown_tokens(self.description),
        )

        section = artifact_kind.construct_section(
            artifact_id=artifact_id,
            raw_section=raw_section,
            section_kind_overrides=section_kind_overrides,
        )

        if self.entity is not None:
            section = section.replace(entity=self.entity)

        if self.entity is not None:
            from donna.machine.templates import DirectiveConfig, DirectiveKind, DirectiveSectionMeta

            if isinstance(self.entity, DirectiveKind):
                directive_config = DirectiveConfig.model_validate(config_data)
                section = section.replace(
                    meta=DirectiveSectionMeta(
                        analyze_id=directive_config.analyze_id,
                        attribute_value=self.entity,
                    )
                )
            elif section.kind == FullArtifactLocalId.parse("donna.operations:python_module"):
                section = section.replace(meta=PythonModuleSectionMeta(attribute_value=self.entity))

        return section


class ArtifactConstructor(BaseEntity):
    title: str
    description: str
    config: ArtifactConfig

    def construct_head(self) -> SectionSource:
        config_data = self.config.model_dump(mode="json")

        config_lines = []

        for key in sorted(config_data.keys()):
            config_lines.append(f"{key} = {_serialize_toml_value(config_data[key])}")

        return SectionSource(
            level=SectionLevel.h1,
            title=self.title,
            configs=[
                CodeSource(
                    format="toml",
                    properties={"donna": True},
                    content="\n".join(config_lines),
                )
            ],
            original_tokens=_markdown_tokens(self.description),
            analysis_tokens=_markdown_tokens(self.description),
        )
