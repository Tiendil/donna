from typing import Any

from donna.core.entities import BaseEntity
from donna.core.errors import EnvironmentError
from donna.domain.ids import ArtifactLocalId, FullArtifactId, FullArtifactLocalId, PythonImportPath
from donna.protocol.cells import Cell


class ArtifactValidationError(EnvironmentError):
    cell_kind: str = "artifact_validation_error"
    code: str
    artifact_id: FullArtifactId
    section_id: ArtifactLocalId | None = None
    message: str

    def content_intro(self) -> str:
        if self.section_id:
            return f"Error in artifact '{self.artifact_id}', section '{self.section_id}'"

        return f"Error in artifact '{self.artifact_id}'"


class MultiplePrimarySectionsError(ArtifactValidationError):
    code: str = "donna.artifacts.multiple_primary_sections"
    message: str = "Artifact must have exactly one primary section, found multiple: `{error.primary_sections}`"
    primary_sections: list[ArtifactLocalId]


class ArtifactSectionConfig(BaseEntity):
    id: ArtifactLocalId
    kind: PythonImportPath


class ArtifactSectionMeta(BaseEntity):
    def cells_meta(self) -> dict[str, Any]:
        return {}


class ArtifactSection(BaseEntity):
    id: ArtifactLocalId
    artifact_id: FullArtifactId
    kind: PythonImportPath
    title: str
    description: str
    primary: bool = False

    meta: ArtifactSectionMeta

    def cells(self) -> list[Cell]:
        return [
            Cell.build_meta(
                kind="artifact_section_meta",
                artifact_id=str(self.artifact_id),
                section_id=str(self.id) if self.id else None,
                section_kind=str(self.kind) if self.kind else None,
                section_title=self.title,
                section_description=self.description,
                section_primary=self.primary,
                **self.meta.cells_meta(),
            )
        ]

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

    def validate_artifact(self) -> list[ArtifactValidationError]:
        from donna.machine.primitives import resolve_primitive

        primary_sections = self._primary_sections()

        errors: list[ArtifactValidationError] = []

        if len(primary_sections) != 1:
            errors.append(
                MultiplePrimarySectionsError(
                    artifact_id=self.id,
                    primary_sections=sorted(section.id for section in primary_sections),
                )
            )

        for section in self.sections:
            primitive = resolve_primitive(section.kind)
            errors.extend(primitive.validate_section(self, section.id))

        return errors

    def cells_info(self) -> list[Cell]:
        primary_section = self.primary_section()
        return [
            Cell.build_meta(
                kind="artifact_info",
                artifact_id=str(self.id),
                artifact_kind=str(primary_section.kind),
                artifact_title=primary_section.title,
                artifact_description=primary_section.description,
            )
        ]

    # TODO: should we attach section cells here as well?
    def cells(self) -> list[Cell]:
        primary_section = self.primary_section()
        cells = [
            Cell.build_meta(
                kind="artifact_meta",
                artifact_id=str(self.id),
                artifact_kind=str(primary_section.kind),
                artifact_title=primary_section.title,
                artifact_description=primary_section.description,
            )
        ]

        markdown = "\n".join(self.markdown_blocks())

        cells.append(Cell.build_markdown(kind="artifact_markdown", content=markdown, artifact_id=str(self.id)))

        return cells

    def get_section(self, section_id: ArtifactLocalId | None) -> ArtifactSection | None:
        if section_id is None:
            return self.primary_section()
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

    def markdown_blocks(self) -> list[str]:
        primary_section = self.primary_section()
        blocks = [f"# {primary_section.title}", primary_section.description]

        for section in self.sections:
            if section.primary:
                continue
            blocks.extend(section.markdown_blocks())

        return blocks


def resolve(target_id: FullArtifactLocalId) -> ArtifactSection:
    from donna.world import artifacts as world_artifacts

    artifact = world_artifacts.load_artifact(target_id.full_artifact_id)
    section = artifact.get_section(target_id.local_id)

    if section is None:
        raise NotImplementedError(f"Section '{target_id}' is not available")

    return section
