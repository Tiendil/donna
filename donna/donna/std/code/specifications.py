from donna.domain.ids import NamespaceId
from donna.machine.artifacts import Artifact, ArtifactInfo, ArtifactKind
from donna.machine.cells import Cell
from donna.world.markdown import ArtifactSource


class Specification(Artifact):
    content: str

    def cells(self) -> list["Cell"]:
        return [Cell.build_markdown(kind=self.info.kind, content=self.content, id=str(self.info.id))]


class SpecificationKind(ArtifactKind):
    def construct(self, source: ArtifactSource) -> "Artifact":  # type: ignore[override]
        description = None

        for config in source.head.configs:
            data = config.structured_data()
            description = data.get("description", description)

        title = source.head.title or str(source.id)
        description = description or ""

        spec = Specification(
            info=ArtifactInfo(kind=self.id, id=source.id, title=title, description=description),
            content=source.as_markdown(),
        )

        return spec


specification_kind = SpecificationKind(
    id="specification",
    namespace_id=NamespaceId("specifications"),
    description="A specification that define various aspects of the current project.",
)
