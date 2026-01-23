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
)
from donna.world import markdown

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class TextConfig(ArtifactSectionConfig):
    pass


class ArtifactSectionTextKind(ArtifactSectionKind):
    def execute_section(self, task: "Task", unit: "WorkUnit", operation: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("Text sections cannot be executed.")

    def from_markdown_section(
        self,
        artifact_id: FullArtifactId,
        source: markdown.SectionSource,
        config: dict[str, object],
    ) -> ArtifactSection:
        data = dict(config)

        if "id" not in data:
            # TODO: we should replace this hack with a proper ID generator
            #       to keep that id stable between runs
            #       options:
            #       - a hash of the content
            #       - a sequential ID generator per artifact
            data["id"] = "text" + uuid.uuid4().hex.replace("-", "")

        parsed_config = TextConfig.parse_obj(data)

        return ArtifactSection(
            id=parsed_config.id,
            kind=parsed_config.kind,
            title=source.title or "",
            description=source.as_original_markdown(with_title=False),
            meta=ArtifactSectionMeta(),
        )


class SpecificationKind(ArtifactKind):
    def construct_artifact(self, source: ArtifactContent, sections: list[ArtifactSection]) -> Artifact:
        title = source.head.title or str(source.id)
        description = source.head.description
        kind_id = ArtifactConfig.parse_obj(source.head.config).kind

        return Artifact(
            id=source.id,
            kind=kind_id,
            title=title,
            description=description,
            meta=ArtifactMeta(),
            sections=sections,
        )
