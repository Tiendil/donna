from donna.machine.artifacts import Artifact, ArtifactKindSection, ArtifactMeta
from donna.world.markdown import ArtifactSource


class SpecificationKind(ArtifactKindSection):
    def construct_artifact(self, source: ArtifactSource) -> "Artifact":
        title = source.head.title or str(source.id)
        description = source.head.as_original_markdown(with_title=False)

        sections = [self.construct_section(source.id, section) for section in source.tail]

        spec = Artifact(
            id=source.id, kind=self.id, title=title, description=description, meta=ArtifactMeta(), sections=sections
        )

        return spec
