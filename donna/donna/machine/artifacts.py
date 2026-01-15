from typing import Any
from donna.core.entities import BaseEntity
from donna.domain.ids import ArtifactKindId, FullArtifactId, NamespaceId, FullArtifactLocalId, ArtifactSectionKindId, ArtifactLocalId
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

    def construct(self, source: ArtifactSource) -> "Artifact":  # type: ignore[override]
        raise NotImplementedError("You must implement this method in subclasses")

    def validate_artifact(self, artifact: "Artifact") -> tuple[bool, list[Cell]]:
        return True, [
            Cell.build_meta(
                kind="artifact_kind_validation",
                id=str(artifact.info.id),
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
    id: FullArtifactLocalId
    kind: ArtifactSectionKindId
    title: str
    description: str

    meta: ArtifactSectionMeta

    def cells(self) -> list[Cell]:
        return [Cell.build_meta(kind="artifact_section",
                                section_id=self.id,
                                section_kind=self.kind,
                                section_title=self.title,
                                section_description=self.description,
                                **self.meta.cells_meta()
                                )]


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
        return [Cell.build_meta(kind="artifact",
                                artifact_id=self.id,
                                artifact_kind=self.kind,
                                artifact_title=self.title,
                                artifact_description=self.description,
                                **self.meta.cells_meta()
                                )]

    def get_section(self, section_id: ArtifactLocalId) -> ArtifactSection | None:
        for section in self.sections:
            if section.id == section_id:
                return section
        return None
