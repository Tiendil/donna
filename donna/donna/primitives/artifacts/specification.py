import uuid
from typing import TYPE_CHECKING, ClassVar, Iterable

from donna.domain.ids import ArtifactLocalId, FullArtifactId
from donna.machine.artifacts import (
    ArtifactPrimarySectionKind,
    ArtifactSection,
    ArtifactSectionConfig,
    ArtifactSectionKind,
)
from donna.world import markdown

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class TextConfig(ArtifactSectionConfig):
    pass


class ArtifactSectionTextKind(ArtifactSectionKind):
    config_class: ClassVar[type[TextConfig]] = TextConfig

    def execute_section(self, task: "Task", unit: "WorkUnit", operation: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("Text sections cannot be executed.")

    def default_section_id(
        self,
        artifact_id: FullArtifactId,
        source: markdown.SectionSource,
        primary: bool = False,
    ) -> ArtifactLocalId | None:
        # TODO: replace this with a stable ID generator.
        return ArtifactLocalId("text" + uuid.uuid4().hex.replace("-", ""))


class SpecificationKind(ArtifactPrimarySectionKind):
    pass
