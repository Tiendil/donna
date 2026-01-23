from types import ModuleType
from typing import TYPE_CHECKING, Any, Iterable

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.ids import ArtifactLocalId, FullArtifactId, FullArtifactLocalId
from donna.machine.cells import Cell
from donna.machine.tasks import Task, WorkUnit

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.world import markdown


class ArtifactKind(BaseEntity):
    default_section_kind: FullArtifactLocalId = FullArtifactLocalId.parse("donna.operations.text")

    def construct_artifact(self, source: "ArtifactContent", sections: list["ArtifactSection"]) -> "Artifact":
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
    id: ArtifactLocalId | None
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

    def get_section(self, section_id: ArtifactLocalId) -> ArtifactSection | None:
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

    def from_markdown_section(
        self,
        artifact_id: FullArtifactId,
        source: "markdown.SectionSource",
        config: dict[str, Any],
    ) -> ArtifactSection:
        raise NotImplementedError("You MUST implement this method.")

    def from_python_section(
        self,
        artifact_id: FullArtifactId,
        module: ModuleType,
        section: "Section",
    ) -> ArtifactSection:
        raise NotImplementedError("You MUST implement this method.")


def resolve(target_id: FullArtifactLocalId) -> ArtifactSection:
    from donna.world import artifacts as world_artifacts

    artifact = world_artifacts.load_artifact(target_id.full_artifact_id)
    section = artifact.get_section(target_id.local_id)

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


class Section(BaseEntity):
    title: str
    description: str
    config: ArtifactSectionConfig
    entity: BaseEntity | None = None


class ArtifactConstructor(BaseEntity):
    title: str
    description: str
    config: ArtifactConfig


def _analysis_text(title: str, description: str) -> str:
    if title:
        return f"## {title}\n{description}"
    return description
