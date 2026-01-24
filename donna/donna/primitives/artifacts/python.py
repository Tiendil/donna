from typing import TYPE_CHECKING, Iterable

from donna.domain.ids import FullArtifactId
from donna.machine.artifacts import (
    ArtifactSection,
    ArtifactSectionConfig,
    ArtifactSectionKind,
)
from donna.world import markdown

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.machine.tasks import Task, WorkUnit


class PythonModuleSectionConfig(ArtifactSectionConfig):
    pass


class PythonModuleSectionKind(ArtifactSectionKind):
    def execute_section(self, task: "Task", unit: "WorkUnit", operation: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("Python module sections cannot be executed.")

    def markdown_construct_section(  # noqa: D401
        self,
        artifact_id: FullArtifactId,
        source: markdown.SectionSource,
        config: dict[str, object],
        primary: bool = False,
    ) -> ArtifactSection:
        raise NotImplementedError("Python module sections cannot be constructed from markdown.")


class PythonArtifact(ArtifactSectionKind):
    pass
