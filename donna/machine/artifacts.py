from typing import Any

import pydantic

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import ArtifactSectionId, FullArtifactId, PythonImportPath
from donna.machine.errors import (
    ArtifactPrimarySectionMissing,
    ArtifactSectionNotFound,
    MultiplePrimarySectionsError,
)
from donna.protocol.cells import Cell
from donna.protocol.nodes import Node


class ArtifactSectionConfig(BaseEntity):
    id: ArtifactSectionId
    kind: PythonImportPath
    tags: list[str] = pydantic.Field(default_factory=list)


class ArtifactSectionMeta(BaseEntity):
    def cells_meta(self) -> dict[str, Any]:
        return {}


class ArtifactSection(BaseEntity):
    id: ArtifactSectionId
    artifact_id: FullArtifactId
    kind: PythonImportPath
    title: str
    description: str
    tags: list[str] = pydantic.Field(default_factory=list)
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

    def primary_section(self) -> Result[ArtifactSection, ErrorsList]:
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

    def validate_artifact(self) -> Result[None, ErrorsList]:  # noqa: CCR001
        from donna.context.context import context

        primary_sections = self._primary_sections()

        errors: ErrorsList = []

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

    def get_section(self, section_id: ArtifactSectionId | None) -> Result[ArtifactSection, ErrorsList]:
        if section_id is None:
            return self.primary_section()
        for section in self.sections:
            if section.id == section_id:
                return Ok(section)
        return Err([ArtifactSectionNotFound(artifact_id=self.id, section_id=section_id)])

    def node(self) -> "ArtifactNode":
        return ArtifactNode(self)

    @unwrap_to_error
    def markdown_blocks(self) -> Result[list[str], ErrorsList]:
        primary_section = self.primary_section().unwrap()
        blocks = [f"# {primary_section.title}", primary_section.description]

        for section in self.sections:
            if section.primary:
                continue
            blocks.extend(section.markdown_blocks())

        return Ok(blocks)


class ArtifactNode(Node):
    __slots__ = ("_artifact",)

    def __init__(self, artifact: Artifact) -> None:
        self._artifact = artifact

    def status(self) -> Cell:
        primary_section_result = self._artifact.primary_section()
        if primary_section_result.is_err():
            return primary_section_result.unwrap_err()[0].node().status()

        primary_section = primary_section_result.unwrap()
        return Cell.build_markdown(
            kind="artifact_status",
            artifact_id=str(self._artifact.id),
            artifact_kind=str(primary_section.kind),
            artifact_title=primary_section.title,
            content=primary_section.description,
        )

    def info(self) -> Cell:
        primary_section_result = self._artifact.primary_section()
        if primary_section_result.is_err():
            return primary_section_result.unwrap_err()[0].node().info()

        primary_section = primary_section_result.unwrap()
        blocks_result = self._artifact.markdown_blocks()
        if blocks_result.is_err():
            return blocks_result.unwrap_err()[0].node().info()

        return Cell.build_markdown(
            kind="artifact_info",
            content="\n".join(blocks_result.unwrap()),
            artifact_id=str(self._artifact.id),
            artifact_kind=str(primary_section.kind),
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
