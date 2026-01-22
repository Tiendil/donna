import uuid
from typing import TYPE_CHECKING, Iterable

from donna.domain.ids import FullArtifactId
from donna.machine.artifacts import (
    Artifact,
    ArtifactConfig,
    ArtifactContent,
    ArtifactKind,
    ArtifactMeta,
    ArtifactSection,
    ArtifactSectionConfig,
    ArtifactSectionKind,
    ArtifactSectionMeta,
    SectionContent,
)

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class TextConfig(ArtifactSectionConfig):
    pass


class ArtifactSectionTextKind(ArtifactSectionKind):
    def execute_section(self, task: "Task", unit: "WorkUnit", operation: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("Text sections cannot be executed.")

    def construct_section(self, artifact_id: FullArtifactId, section: SectionContent) -> ArtifactSection:
        data = dict(section.config)

        if "id" not in data:
            # TODO: we should replace this hack with a proper ID generator
            #       to keep that id stable between runs
            #       options:
            #       - a hash of the content
            #       - a sequential ID generator per artifact
            data["id"] = "text" + uuid.uuid4().hex.replace("-", "")

        config = TextConfig.parse_obj(data)

        return ArtifactSection(
            id=artifact_id.to_full_local(config.id),
            kind=config.kind,
            title=section.title,
            description=section.description,
            meta=ArtifactSectionMeta(),
        )


class SpecificationKind(ArtifactKind):
    def construct_artifact(self, source: ArtifactContent) -> Artifact:
        title = source.head.title or str(source.id)
        description = source.head.description
        kind_id = ArtifactConfig.parse_obj(source.head.config).kind

        sections = [self.construct_section(source.id, section) for section in source.tail]

        return Artifact(
            id=source.id,
            kind=kind_id,
            title=title,
            description=description,
            meta=ArtifactMeta(),
            sections=sections,
        )
