import types
from typing import TYPE_CHECKING, Iterable

from donna.domain.ids import FullArtifactId, FullArtifactLocalId
from donna.machine.artifacts import (
    Artifact,
    ArtifactContent,
    ArtifactKind,
    ArtifactSection,
    ArtifactSectionConfig,
    ArtifactSectionKind,
    ArtifactSectionMeta,
    Section,
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

    def from_markdown_section(  # noqa: D401
        self,
        artifact_id: FullArtifactId,
        source: markdown.SectionSource,
        config: dict[str, object],
    ) -> ArtifactSection:
        raise NotImplementedError("Python module sections cannot be constructed from markdown.")

    def from_python_section(
        self,
        artifact_id: FullArtifactId,
        module: types.ModuleType,
        section: Section,
    ) -> ArtifactSection:
        data = section.config.model_dump(mode="python")
        config_data = {
            "id": data.get("id"),
            "kind": data.get("kind"),
        }
        config = PythonModuleSectionConfig.parse_obj(config_data)

        return ArtifactSection(
            id=config.id,
            kind=config.kind,
            title=section.title,
            description=section.description,
            meta=ArtifactSectionMeta(),
        )


class PythonArtifact(ArtifactKind):
    def construct_artifact(self, source: ArtifactContent, sections: list[ArtifactSection]) -> Artifact:
        raise NotImplementedError("Python artifacts are constructed from modules, not markdown sources.")

    def construct_module_artifact(  # noqa: CCR001
        self,
        module: types.ModuleType,
        artifact_id: FullArtifactId,
        kind_id: FullArtifactLocalId,
    ) -> Artifact | None:
        raise NotImplementedError("Python artifacts are constructed via the python source module.")
