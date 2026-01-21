from donna.machine.artifacts import Artifact, ArtifactConfig, ArtifactContent, ArtifactKind, ArtifactMeta


class SpecificationKind(ArtifactKind):
    def construct_artifact(self, source: ArtifactContent) -> "Artifact":
        title = source.head.title or str(source.id)
        description = source.head.description
        kind_id = ArtifactConfig.parse_obj(source.head.config).kind

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
