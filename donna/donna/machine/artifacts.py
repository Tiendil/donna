import types
import uuid
from typing import TYPE_CHECKING, Any, Iterable

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.ids import ArtifactLocalId, FullArtifactId, FullArtifactLocalId
from donna.machine.cells import Cell
from donna.machine.tasks import Task, WorkUnit

if TYPE_CHECKING:
    from donna.machine.changes import Change


class ArtifactKind(BaseEntity):
    default_section_kind: FullArtifactLocalId = FullArtifactLocalId.parse("donna.operations.text")

    def construct_section(
        self,
        artifact_id: FullArtifactId,
        section: "SectionContent",
        section_kind_overrides: dict[FullArtifactLocalId, "ArtifactSectionKind"] | None = None,
    ) -> "ArtifactSection":
        data = dict(section.config)

        if "kind" not in data:
            data["kind"] = self.default_section_kind

        kind_value = data["kind"]
        if isinstance(kind_value, str):
            section_kind_id = FullArtifactLocalId.parse(kind_value)
        else:
            section_kind_id = kind_value

        section_kind = None
        if section_kind_overrides is not None:
            section_kind = section_kind_overrides.get(section_kind_id)

        if section_kind is None:
            resolved_section = resolve(section_kind_id)
            if not isinstance(resolved_section.meta, ArtifactSectionKindMeta):
                raise NotImplementedError(f"Section kind '{section_kind_id}' is not available")
            section_kind = resolved_section.meta.section_kind

        section_content = section.replace(config=data)
        return section_kind.construct_section(artifact_id, section_content)

    def construct_artifact(self, source: "ArtifactContent") -> "Artifact":
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
    model_config = pydantic.ConfigDict(extra="ignore")

    kind: FullArtifactLocalId


class ArtifactSectionMeta(BaseEntity):
    def cells_meta(self) -> dict[str, Any]:
        return {}


class ArtifactKindSectionMeta(ArtifactSectionMeta):
    artifact_kind: "ArtifactKind"

    model_config = BaseEntity.model_config | {"arbitrary_types_allowed": True}

    def cells_meta(self) -> dict[str, Any]:
        return {"artifact_kind": repr(self.artifact_kind)}


class ArtifactSectionKindMeta(ArtifactSectionMeta):
    section_kind: "ArtifactSectionKind"

    model_config = BaseEntity.model_config | {"arbitrary_types_allowed": True}

    def cells_meta(self) -> dict[str, Any]:
        return {"section_kind": repr(self.section_kind)}


class ArtifactSection(BaseEntity):
    # some section may have no id and kind — it is ok for simple text sections
    id: FullArtifactLocalId | None
    kind: FullArtifactLocalId | None
    title: str
    description: str

    meta: ArtifactSectionMeta

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

    def construct_section(self, artifact_id: FullArtifactId, section: "SectionContent") -> ArtifactSection:
        raise NotImplementedError("You MUST implement this method.")


class TextConfig(ArtifactSectionConfig):
    pass


class PythonModuleSectionConfig(ArtifactSectionConfig):
    pass


class ArtifactSectionTextKind(ArtifactSectionKind):

    def execute_section(self, task: Task, unit: WorkUnit, operation: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("Text sections cannot be executed.")

    def construct_section(self, artifact_id: FullArtifactId, section: "SectionContent") -> ArtifactSection:
        data = dict(section.config)

        if "id" not in data:
            # TODO: we should replace this hack with a proper ID generator
            #       to keep that id stable between runs
            #       options:
            #       - a hash of the content
            #       - a sequential ID generator per artifact
            data["id"] = "text" + uuid.uuid4().hex.replace("-", "")

        config = TextConfig.parse_obj(data)

        return ArtifactSection(
            id=artifact_id.to_full_local(config.id),
            kind=config.kind,
            title=section.title,
            description=section.description,
            meta=ArtifactSectionMeta(),
        )


class PythonModuleSectionKind(ArtifactSectionKind):

    def execute_section(self, task: Task, unit: WorkUnit, operation: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("Python module sections cannot be executed.")

    def construct_section(self, artifact_id: FullArtifactId, section: "SectionContent") -> ArtifactSection:
        data = dict(section.config)
        config_data = {
            "id": data.get("id"),
            "kind": data.get("kind"),
        }
        config = PythonModuleSectionConfig.parse_obj(config_data)

        return ArtifactSection(
            id=artifact_id.to_full_local(config.id),
            kind=config.kind,
            title=section.title,
            description=section.description,
            meta=ArtifactSectionMeta(),
        )


class PythonArtifact(ArtifactKind):

    def construct_artifact(self, source: "ArtifactContent") -> "Artifact":
        raise NotImplementedError("Python artifacts are constructed from modules, not markdown sources.")

    def construct_module_artifact(  # noqa: CCR001
        self,
        module: types.ModuleType,
        artifact_id: FullArtifactId,
        kind_id: FullArtifactLocalId,
    ) -> "Artifact | None":
        artifact_constructor: ArtifactConstructor | None = None

        for value in module.__dict__.values():
            if isinstance(value, ArtifactConstructor):
                if artifact_constructor is not None:
                    raise NotImplementedError("Artifact module must define only one ArtifactConstructor.")

                artifact_constructor = value

        if artifact_constructor is None:
            return None

        title = artifact_constructor.title
        description = artifact_constructor.description
        artifact_kind_id = artifact_constructor.config.kind

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


def resolve(target_id: FullArtifactLocalId) -> ArtifactSection:
    from donna.world import artifacts as world_artifacts

    artifact = world_artifacts.load_artifact(target_id.full_artifact_id)
    section = artifact.get_section(target_id)

    if section is None:
        raise NotImplementedError(f"Section '{target_id}' is not available")

    return section


class SectionContent(BaseEntity):
    title: str
    description: str
    analysis: str
    config: dict[str, Any]


class ArtifactContent(BaseEntity):
    id: FullArtifactId
    head: SectionContent
    tail: list[SectionContent]


class SectionConstructor(BaseEntity):
    title: str
    description: str
    config: ArtifactSectionConfig
    entity: BaseEntity | None = None

    def build_section(
        self,
        artifact_kind: ArtifactKind,
        artifact_id: FullArtifactId,
        section_kind_overrides: dict[FullArtifactLocalId, ArtifactSectionKind] | None = None,
    ) -> ArtifactSection:
        config_data = self.config.model_dump(mode="python")
        analysis = _analysis_text(self.title, self.description)

        section = artifact_kind.construct_section(
            artifact_id=artifact_id,
            section=SectionContent(
                title=self.title,
                description=self.description,
                analysis=analysis,
                config=config_data,
            ),
            section_kind_overrides=section_kind_overrides,
        )

        if self.entity is None:
            return section

        from donna.machine.templates import DirectiveConfig, DirectiveKind, DirectiveSectionMeta

        if isinstance(self.entity, DirectiveKind):
            directive_config = DirectiveConfig.model_validate(config_data)
            return section.replace(
                meta=DirectiveSectionMeta(
                    analyze_id=directive_config.analyze_id,
                    directive=self.entity,
                )
            )

        if isinstance(self.entity, ArtifactKind):
            return section.replace(meta=ArtifactKindSectionMeta(artifact_kind=self.entity))

        if isinstance(self.entity, ArtifactSectionKind):
            return section.replace(meta=ArtifactSectionKindMeta(section_kind=self.entity))

        raise NotImplementedError(f"Unsupported section entity type: {type(self.entity).__name__}")


class ArtifactConstructor(BaseEntity):
    title: str
    description: str
    config: ArtifactConfig


def _analysis_text(title: str, description: str) -> str:
    if title:
        return f"## {title}\n{description}"
    return description
