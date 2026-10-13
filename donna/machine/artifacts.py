from llm_tool_cli.core.entities import BaseEntity
from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Err, Ok, Result
from llm_tool_cli.protocol.logic_cells import EnvironmentErrorCell

from donna.domain.artifact_ids import ArtifactId
from donna.domain.ids import SectionId
from donna.domain.python_path import PythonPath
from donna.machine.caches import caches
from donna.machine.errors import ArtifactPrimarySectionMissing, ArtifactSectionNotFound, MultiplePrimarySectionsError
from donna.protocol import ArtifactStatusCell


class ArtifactSectionConfig(BaseEntity):
    id: SectionId
    kind: PythonPath


class ArtifactSectionMeta(BaseEntity):
    pass


class ArtifactSection(BaseEntity):
    id: SectionId
    artifact_id: ArtifactId
    kind: PythonPath
    title: str
    description: str
    primary: bool = False

    meta: ArtifactSectionMeta


class Artifact(BaseEntity):
    id: ArtifactId

    sections: list[ArtifactSection]

    def _primary_sections(self) -> list[ArtifactSection]:
        return [section for section in self.sections if section.primary]

    def primary_section(self) -> Result[ArtifactSection]:
        primary_sections = self._primary_sections()
        if len(primary_sections) == 0:
            return Err([ArtifactPrimarySectionMissing(artifact_id=self.id)])
        if len(primary_sections) > 1:
            return Err(
                [
                    MultiplePrimarySectionsError(
                        artifact_id=self.id,
                        primary_sections=sorted(section.id for section in primary_sections),
                    )
                ]
            )
        return Ok(primary_sections[0])

    def validate_artifact(self) -> Result[None]:  # noqa: CCR001
        primary_sections = self._primary_sections()

        errors: EnvironmentErrors = []

        if len(primary_sections) == 0:
            errors.append(ArtifactPrimarySectionMissing(artifact_id=self.id))
        elif len(primary_sections) > 1:
            errors.append(
                MultiplePrimarySectionsError(
                    artifact_id=self.id,
                    primary_sections=sorted(section.id for section in primary_sections),
                )
            )

        for section in self.sections:
            primitive_result = caches.get().primitives.resolve(section.kind)
            if primitive_result.is_err():
                errors.extend(primitive_result.unwrap_err())
                continue

            primitive = primitive_result.unwrap()
            result = primitive.validate_section(self, section.id)

            if result.is_ok():
                continue

            errors.extend(result.unwrap_err())

        if errors:
            return Err(errors)

        return Ok(None)

    def get_section(self, section_id: SectionId | None) -> Result[ArtifactSection]:
        if section_id is None:
            return self.primary_section()
        for section in self.sections:
            if section.id == section_id:
                return Ok(section)
        return Err([ArtifactSectionNotFound(artifact_id=self.id, section_id=section_id)])

    def get_section_number(self, section_id: SectionId) -> int | None:
        for index, section in enumerate(self.sections):
            if section.id == section_id:
                return index

        return None

    def status_cell(self) -> ArtifactStatusCell | EnvironmentErrorCell:
        primary_section_result = self.primary_section()
        if primary_section_result.is_err():
            return EnvironmentErrorCell(error=primary_section_result.unwrap_err()[0])
        primary_section = primary_section_result.unwrap()
        return ArtifactStatusCell(
            artifact_id=self.id,
            artifact_kind=primary_section.kind,
            artifact_title=primary_section.title,
            description=primary_section.description,
        )
