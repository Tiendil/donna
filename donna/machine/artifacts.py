from collections.abc import Mapping

from llm_tool_cli.core.entities import BaseEntity
from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Err, Ok, Result
from llm_tool_cli.protocol.logic_cells import EnvironmentErrorCell
from llm_tool_cli.protocol.output_cells.base import MetaValue

from donna.domain.artifact_ids import ArtifactId
from donna.domain.ids import SectionId
from donna.domain.python_path import PythonPath
from donna.machine.context import context
from donna.machine.errors import ArtifactPrimarySectionMissing, ArtifactSectionNotFound, MultiplePrimarySectionsError
from donna.protocol import ArtifactInfoCell, ArtifactSectionStatusCell, ArtifactStatusCell
from donna.protocol.errors import environment_error_node
from donna.protocol.nodes import Node


class ArtifactSectionConfig(BaseEntity):
    id: SectionId
    kind: PythonPath


class ArtifactSectionMeta(BaseEntity):
    def cells_meta(self) -> Mapping[str, MetaValue]:
        return {}


class ArtifactSection(BaseEntity):
    id: SectionId
    artifact_id: ArtifactId
    kind: PythonPath
    title: str
    description: str
    primary: bool = False

    meta: ArtifactSectionMeta

    def node(self) -> "ArtifactSectionNode":
        return ArtifactSectionNode(self)


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
            primitive_result = context().primitives.resolve(section.kind)
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

    def node(self) -> "ArtifactNode":
        return ArtifactNode(self)


class ArtifactNode(Node):
    __slots__ = ("_artifact",)

    def __init__(self, artifact: Artifact) -> None:
        self._artifact = artifact

    def status(self) -> ArtifactStatusCell | EnvironmentErrorCell:
        primary_section_result = self._artifact.primary_section()
        if primary_section_result.is_err():
            return environment_error_node(primary_section_result.unwrap_err()[0]).status()
        primary_section = primary_section_result.unwrap()
        return ArtifactStatusCell(
            artifact_id=self._artifact.id,
            artifact_kind=primary_section.kind,
            artifact_title=primary_section.title,
            description=primary_section.description,
        )

    def info(self) -> ArtifactInfoCell | EnvironmentErrorCell:
        primary_section_result = self._artifact.primary_section()
        if primary_section_result.is_err():
            return environment_error_node(primary_section_result.unwrap_err()[0]).status()
        primary_section = primary_section_result.unwrap()
        return ArtifactInfoCell(
            artifact_id=self._artifact.id,
            artifact_kind=primary_section.kind,
            title=primary_section.title,
            description=primary_section.description,
            sections=tuple(
                ArtifactSectionStatusCell(
                    artifact_id=section.artifact_id,
                    section_id=section.id,
                    section_kind=section.kind,
                    section_primary=section.primary,
                    title=section.title,
                    description=section.description,
                )
                for section in self._artifact.sections
                if not section.primary
            ),
        )

    def components(self) -> list["Node"]:
        return [ArtifactSectionNode(section) for section in self._artifact.sections]


class ArtifactSectionNode(Node):
    __slots__ = ("_section",)

    def __init__(self, section: ArtifactSection) -> None:
        self._section = section

    def status(self) -> ArtifactSectionStatusCell:
        return ArtifactSectionStatusCell(
            artifact_id=self._section.artifact_id,
            section_id=self._section.id,
            section_kind=self._section.kind,
            section_primary=self._section.primary,
            title=self._section.title,
            description=self._section.description,
            extra_meta=dict(self._section.meta.cells_meta()),
        )
