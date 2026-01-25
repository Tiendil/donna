import importlib
from typing import TYPE_CHECKING, Any, ClassVar, Iterable

from donna.core.entities import BaseEntity
from donna.domain.ids import ArtifactLocalId, FullArtifactId, FullArtifactLocalId, PythonImportPath
from donna.machine.cells import Cell
from donna.machine.tasks import Task, WorkUnit

if TYPE_CHECKING:
    from donna.machine.changes import Change


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
            section_kind = resolve_section_kind(section.kind)
            is_valid, cells = section_kind.validate_section(self, section.id)

            if not is_valid:
                return is_valid, cells

        return True, []

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


class ArtifactSectionKind(BaseEntity):
    config_class: ClassVar[type[ArtifactSectionConfig]] = ArtifactSectionConfig

    def execute_section(self, task: Task, unit: WorkUnit, section: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("You MUST implement this method.")

    def validate_section(self, artifact: "Artifact", section_id: ArtifactLocalId) -> tuple[bool, list[Cell]]:
        return True, []


def resolve(target_id: FullArtifactLocalId) -> ArtifactSection:
    from donna.world import artifacts as world_artifacts

    artifact = world_artifacts.load_artifact(target_id.full_artifact_id)
    section = artifact.get_section(target_id.local_id)

    if section is None:
        raise NotImplementedError(f"Section '{target_id}' is not available")

    return section


def resolve_section_kind(section_kind_id: PythonImportPath | str) -> ArtifactSectionKind:
    if isinstance(section_kind_id, PythonImportPath):
        import_path = str(section_kind_id)
    else:
        import_path = str(PythonImportPath.parse(section_kind_id))

    if "." not in import_path:
        raise NotImplementedError(f"Section kind '{import_path}' is not a valid import path")

    module_path, kind_name = import_path.rsplit(".", maxsplit=1)

    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        raise NotImplementedError(f"Section kind module '{module_path}' is not importable") from exc

    try:
        kind = getattr(module, kind_name)
    except AttributeError as exc:
        raise NotImplementedError(f"Section kind '{import_path}' is not available") from exc

    if not isinstance(kind, ArtifactSectionKind):
        raise NotImplementedError(f"Section kind '{import_path}' is not a section kind")

    return kind
