from donna.world.artifact.source import ArtifactSource
from donna.machine.artifacts import ArtifactKind, Artifact, ArtifactInfo
from donna.machine.cells import Cell


class Specification(Artifact):
    content: str

    def cells(self) -> list['Cell']:
        raise NotImplementedError("You must implement this method in subclasses")


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
                title=source.header.title,
                description=description
            ),
            content=source.as_markdown()
        )

        return spec


specification_kind = SpecificationKind(
    id="specification",
    name="specification",
    description="A specification that define various aspects of the current project.",
)
