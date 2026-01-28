from typing import Any

from donna.core.entities import BaseEntity
from donna.core.errors import EnvironmentError, ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import ArtifactSectionId, FullArtifactId, FullArtifactSectionId, PythonImportPath
from donna.protocol.cells import Cell
from donna.protocol.nodes import Node


class ArtifactValidationError(EnvironmentError):
    cell_kind: str = "artifact_validation_error"
    artifact_id: FullArtifactId
    section_id: ArtifactSectionId | None = None

    def content_intro(self) -> str:
        if self.section_id:
            return f"Error in artifact '{self.artifact_id}', section '{self.section_id}'"

        return f"Error in artifact '{self.artifact_id}'"


class MultiplePrimarySectionsError(ArtifactValidationError):
    code: str = "donna.artifacts.multiple_primary_sections"
    message: str = "Artifact must have exactly one primary section, found multiple: `{error.primary_sections}`"
    ways_to_fix: list[str] = ["Keep a single h1 section in the artifact."]
    primary_sections: list[ArtifactSectionId]


class ArtifactSectionConfig(BaseEntity):
    id: ArtifactSectionId
    kind: PythonImportPath


class ArtifactSectionMeta(BaseEntity):
    def cells_meta(self) -> dict[str, Any]:
        return {}


class ArtifactSection(BaseEntity):
    id: ArtifactSectionId
    artifact_id: FullArtifactId
    kind: PythonImportPath
    title: str
    description: str
    primary: bool = False

    meta: ArtifactSectionMeta

    def node(self) -> "ArtifactSectionNode":
        return ArtifactSectionNode(self)

    def markdown_blocks(self) -> list[str]:
        return [f"## {self.title}", self.description]


class Artifact(BaseEntity):
    id: FullArtifactId

    sections: list[ArtifactSection]

    def _primary_sections(self) -> list[ArtifactSection]:
        return [section for section in self.sections if section.primary]

    def primary_section(self) -> ArtifactSection:
        primary_sections = self._primary_sections()
        if len(primary_sections) != 1:
            raise NotImplementedError(
                f"Artifact '{self.id}' must have exactly one primary section, found {len(primary_sections)}."
            )
        return primary_sections[0]

    def validate_artifact(self) -> Result[None, ErrorsList]:
        from donna.machine.primitives import resolve_primitive

        primary_sections = self._primary_sections()

        errors: ErrorsList = []

        if len(primary_sections) != 1:
            errors.append(
                MultiplePrimarySectionsError(
                    artifact_id=self.id,
                    primary_sections=sorted(section.id for section in primary_sections),
                )
            )

        for section in self.sections:
            primitive = resolve_primitive(section.kind)
            result = primitive.validate_section(self, section.id)

            if result.is_ok():
                continue

            errors.extend(result.unwrap_err())

        if errors:
            return Err(errors)

        return Ok(None)

    def get_section(self, section_id: ArtifactSectionId | None) -> ArtifactSection | None:
        if section_id is None:
            return self.primary_section()
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

    def node(self) -> "ArtifactNode":
        return ArtifactNode(self)

    def markdown_blocks(self) -> list[str]:
        primary_section = self.primary_section()
        blocks = [f"# {primary_section.title}", primary_section.description]

        for section in self.sections:
            if section.primary:
                continue
            blocks.extend(section.markdown_blocks())

        return blocks


class ArtifactNode(Node):
    __slots__ = ("_artifact",)

    def __init__(self, artifact: Artifact) -> None:
        self._artifact = artifact

    def status(self) -> Cell:
        primary_section = self._artifact.primary_section()
        return Cell.build_meta(
            kind="artifact_status",
            artifact_id=str(self._artifact.id),
            artifact_kind=str(primary_section.kind),
            artifact_title=primary_section.title,
            artifact_description=primary_section.description,
        )

    def info(self) -> Cell:
        primary_section = self._artifact.primary_section()

        return Cell.build_markdown(
            kind="artifact_info",
            content="\n".join(self._artifact.markdown_blocks()),
            artifact_id=str(self._artifact.id),
            artifact_kind=str(primary_section.kind),
            artifact_title=primary_section.title,
            artifact_description=primary_section.description,
        )

    def components(self) -> list["Node"]:
        return [ArtifactSectionNode(section) for section in self._artifact.sections]


class ArtifactSectionNode(Node):
    __slots__ = ("_section",)

    def __init__(self, section: ArtifactSection) -> None:
        self._section = section

    def status(self) -> Cell:
        return Cell.build_markdown(
            kind="artifact_section_status",
            content="\n".join(self._section.markdown_blocks()),
            artifact_id=str(self._section.artifact_id),
            section_id=str(self._section.id),
            section_kind=str(self._section.kind),
            section_primary=self._section.primary,
            **self._section.meta.cells_meta(),
        )


def resolve(target_id: FullArtifactSectionId) -> Result[ArtifactSection, ErrorsList]:
    from donna.world import artifacts as world_artifacts

    artifact_result = world_artifacts.load_artifact(target_id.full_artifact_id)
    if artifact_result.is_err():
        return Err(artifact_result.unwrap_err())
    artifact = artifact_result.unwrap()
    section = artifact.get_section(target_id.local_id)

    if section is None:
        raise NotImplementedError(f"Section '{target_id}' is not available")

    return Ok(section)
