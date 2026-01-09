from donna.core.entities import BaseEntity
from donna.domain.ids import FullArtifactId, NamespaceId
from donna.machine.cells import Cell
from donna.world.markdown import ArtifactSource


class ArtifactKind(BaseEntity):
    id: str
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


class ArtifactInfo(BaseEntity):
    kind: str
    id: FullArtifactId
    title: str
    description: str

    def cells(self) -> list[Cell]:
        return [
            Cell.build_meta(
                kind="artifact_info",
                id=str(self.id),
                title=self.title,
                description=self.description,
            )
        ]


class Artifact(BaseEntity):
    info: ArtifactInfo

    def cells(self) -> list[Cell]:
        raise NotImplementedError("You must implement this method in subclasses")
