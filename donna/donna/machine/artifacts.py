import inspect
import types
import uuid
from typing import TYPE_CHECKING, Any, Iterable

from donna.core.entities import BaseEntity
from donna.domain.ids import (
    ArtifactLocalId,
    FullArtifactId,
    FullArtifactLocalId,
    NamespaceId,
)
from donna.machine.cells import Cell
from donna.machine.tasks import Task, WorkUnit
from donna.world.markdown import ArtifactSource, SectionSource

if TYPE_CHECKING:
    from donna.machine.changes import Change


class ArtifactKind(BaseEntity):
    id: FullArtifactLocalId
    description: str
    namespace_id: NamespaceId
    default_section_kind: FullArtifactLocalId = FullArtifactLocalId.parse("donna.python.ops:text")

    def cells(self) -> list[Cell]:
        return [
            Cell.build_meta(
                kind="artifact_kind", id=str(self.id), namespace_id=self.namespace_id, description=self.description
            )
        ]

    def construct_section(self, artifact_id: FullArtifactId, raw_section: SectionSource) -> "ArtifactSection":
        data = raw_section.merged_configs()

        if "kind" not in data:
            data["kind"] = self.default_section_kind

        kind_value = data["kind"]
        if isinstance(kind_value, str):
            section_kind_id = FullArtifactLocalId.parse(kind_value)
        else:
            section_kind_id = kind_value

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
    model_config = BaseEntity.model_config | {"extra": "allow"}


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
    id: FullArtifactLocalId
    title: str

    def execute_section(self, task: Task, unit: WorkUnit, section: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("You MUST implement this method.")

    def construct_section(self, artifact_id: FullArtifactId, raw_section: SectionSource) -> ArtifactSection:
        raise NotImplementedError("You MUST implement this method.")

    def cells(self) -> list[Cell]:
        return [Cell.build_meta(kind="section_kind", id=str(self.id), title=self.title)]


class ArtifactSectionKindSection(ArtifactSection, ArtifactSectionKind):
    id: FullArtifactLocalId
    kind: FullArtifactLocalId | None = None
    description: str = ""
    meta: ArtifactSectionMeta = ArtifactSectionMeta()


class ArtifactKindSection(ArtifactSection, ArtifactKind):
    id: FullArtifactLocalId
    kind: FullArtifactLocalId | None = None
    description: str = ""
    meta: ArtifactSectionMeta = ArtifactSectionMeta()


class TextConfig(ArtifactSectionConfig):
    pass


class ArtifactSectionTextKind(ArtifactSectionKindSection):

    def execute_section(self, task: Task, unit: WorkUnit, operation: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("Text sections cannot be executed.")

    def construct_section(self, artifact_id: FullArtifactId, raw_section: SectionSource) -> ArtifactSection:
        data = raw_section.merged_configs()

        if "kind" not in data:
            data["kind"] = self.id

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
            kind=self.id,
            title=title,
            description=raw_section.as_original_markdown(with_title=False),
            meta=ArtifactSectionMeta(),
        )


class PythonModuleSectionMeta(ArtifactSectionMeta):
    attribute_value: Any

    model_config = BaseEntity.model_config | {"arbitrary_types_allowed": True}

    def cells_meta(self) -> dict[str, Any]:
        return {"attribute_value": repr(self.attribute_value)}


class PythonModuleSectionKind(ArtifactSectionKindSection):

    def execute_section(self, task: Task, unit: WorkUnit, operation: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("Python module sections cannot be executed.")

    def construct_section(self, artifact_id: FullArtifactId, raw_section: SectionSource) -> ArtifactSection:
        raise NotImplementedError("Python module sections are constructed from module attributes.")

    def build_section(self, artifact_id: FullArtifactId, name: str, value: Any) -> ArtifactSection:
        description = inspect.getdoc(value) or ""

        return ArtifactSection(
            id=artifact_id.to_full_local(ArtifactLocalId(name)),
            kind=self.id,
            title=name,
            description=description,
            meta=PythonModuleSectionMeta(attribute_value=value),
        )


class PythonArtifact(ArtifactKindSection):

    def construct_artifact(self, source: ArtifactSource) -> "Artifact":
        raise NotImplementedError("Python artifacts are constructed from modules, not markdown sources.")

    def construct_module(self, module: types.ModuleType, artifact_id: FullArtifactId) -> "Artifact":  # noqa: CCR001
        description = inspect.getdoc(module) or ""
        title = module.__name__

        sections: list[ArtifactSection] = []

        for name, value in sorted(module.__dict__.items()):
            if not name.isidentifier():
                continue

            if name.startswith("_"):
                continue

            if isinstance(value, ArtifactSection):
                if not isinstance(value, (ArtifactSectionKind, ArtifactKind)):
                    raise NotImplementedError(
                        f"Section '{name}' must be an ArtifactSectionKind or ArtifactKind to be included."
                    )

                if value.id is None or value.id.full_artifact_id != artifact_id:
                    raise NotImplementedError(
                        f"Section '{name}' must belong to artifact '{artifact_id}' to be included."
                    )

                sections.append(value)

        return Artifact(
            id=artifact_id,
            kind=self.id,
            title=title,
            description=description,
            meta=ArtifactMeta(),
            sections=sections,
        )


def resolve_section_kind(section_kind_id: FullArtifactLocalId) -> ArtifactSectionKind:
    from donna.world import artifacts as world_artifacts

    artifact = world_artifacts.load_artifact(section_kind_id.full_artifact_id)
    section = artifact.get_section(section_kind_id)

    if section is None or not isinstance(section, ArtifactSectionKind):
        raise NotImplementedError(f"Section kind '{section_kind_id}' is not available")

    return section


def resolve_artifact_kind(artifact_kind_id: FullArtifactLocalId) -> ArtifactKind:
    from donna.world import artifacts as world_artifacts

    artifact = world_artifacts.load_artifact(artifact_kind_id.full_artifact_id)
    section = artifact.get_section(artifact_kind_id)

    if section is None or not isinstance(section, ArtifactKind):
        raise NotImplementedError(f"Artifact kind '{artifact_kind_id}' is not available")

    return section
