from donna.machine.artifacts import Artifact, ArtifactConfig, ArtifactKind, ArtifactMeta
from donna.world.markdown import ArtifactSource


class SpecificationKind(ArtifactKind):
    def construct_artifact(self, source: ArtifactSource) -> "Artifact":
        title = source.head.title or str(source.id)
        description = source.head.as_original_markdown(with_title=False)
        kind_id = ArtifactConfig.parse_obj(source.head.merged_configs()).kind

        sections = [self.construct_section(source.id, section) for section in source.tail]

        spec = Artifact(
            id=source.id,
            kind=kind_id,
            title=title,
            description=description,
            meta=ArtifactMeta(),
            sections=sections,
        )

        return spec
