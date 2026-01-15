from typing import Any

from donna.core.entities import BaseEntity
from donna.domain.ids import (
    ArtifactKindId,
    ArtifactLocalId,
    ArtifactSectionKindId,
    FullArtifactId,
    FullArtifactLocalId,
    NamespaceId,
)
from donna.machine.cells import Cell
from donna.world.markdown import ArtifactSource


class ArtifactKind(BaseEntity):
    id: ArtifactKindId
    description: str
    namespace_id: NamespaceId

    def cells(self) -> list[Cell]:
        return [
            Cell.build_meta(
                kind="artifact_kind", id=self.id, namespace_id=self.namespace_id, description=self.description
            )
        ]

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
    kind: ArtifactSectionKindId


class ArtifactSectionMeta(BaseEntity):
    def cells_meta(self) -> dict[str, Any]:
        return {}


class ArtifactSection(BaseEntity):
    # some section may have no id and kind — it is ok for simple text sections
    id: FullArtifactLocalId | None
    kind: ArtifactSectionKindId | None
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
    kind: ArtifactKindId
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
                artifact_kind=self.kind,
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
