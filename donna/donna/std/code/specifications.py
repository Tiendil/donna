from donna.world.artifact_source import ArtifactSource
from donna.machine.artifacts import ArtifactKind, Artifact, ArtifactInfo
from donna.machine.cells import Cell


class Specification(Artifact):
    content: str

    def cells(self) -> list['Cell']:
        return [Cell.build_markdown(
            kind="specification",
            content=self.content,
            id=self.info.id,
            world_id=self.info.world_id)]


class SpecificationKind(ArtifactKind):

    def construct(self, source: ArtifactSource) -> 'Artifact':
        description = None

        for config in source.head.configs:
            data = config.structured_data()
            description = data.get("description", description)

        spec = Specification(
            info=ArtifactInfo(
                kind=self.id,
                id=source.id,
                world_id=source.world_id,
                title=source.head.title,
                description=description
            ),
            content=source.as_markdown()
        )

        return spec


specification_kind = SpecificationKind(
    id="specifications",
    namespace="specifications",
    description="A specification that define various aspects of the current project.",
)
