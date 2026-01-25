from typing import Any

from donna.core.entities import BaseEntity
from donna.domain.ids import ArtifactLocalId, FullArtifactId, FullArtifactLocalId, PythonImportPath
from donna.machine.cells import Cell


class ArtifactSectionConfig(BaseEntity):
    id: ArtifactLocalId
    kind: PythonImportPath


class ArtifactSectionMeta(BaseEntity):
    def cells_meta(self) -> dict[str, Any]:
        return {}


class ArtifactSection(BaseEntity):
    id: ArtifactLocalId
    kind: PythonImportPath
    title: str
    description: str
    primary: bool = False

    meta: ArtifactSectionMeta

    def cells(self) -> list[Cell]:
        return [
            Cell.build_meta(
                kind="artifact_section_meta",
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

    def validate(self) -> tuple[bool, list[Cell]]:  # type: ignore[override]  # noqa: CCR001
        from donna.machine.primitives import resolve_primitive

        primary_sections = self._primary_sections()

        if len(primary_sections) != 1:
            return False, [
                Cell.build_meta(
                    kind="artifact_kind_validation",
                    id=str(self.id),
                    status="failure",
                    message=f"Artifact must have exactly one primary section, found {len(primary_sections)}.",
                )
            ]

        for section in self.sections:
            primitive = resolve_primitive(section.kind)
            is_valid, cells = primitive.validate_section(self, section.id)

            if not is_valid:
                return is_valid, cells

        return True, []

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
