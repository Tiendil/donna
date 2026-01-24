import uuid
from typing import TYPE_CHECKING, Any, ClassVar, Iterable

from donna.core.entities import BaseEntity
from donna.domain.ids import ArtifactLocalId, FullArtifactId, FullArtifactLocalId
from donna.machine.cells import Cell
from donna.machine.tasks import Task, WorkUnit

if TYPE_CHECKING:
    from donna.machine.changes import Change
    from donna.world import markdown


class ArtifactSectionConfig(BaseEntity):
    id: ArtifactLocalId
    kind: FullArtifactLocalId


class ArtifactSectionMeta(BaseEntity):
    def cells_meta(self) -> dict[str, Any]:
        return {}


class ArtifactSectionKindMeta(ArtifactSectionMeta):
    section_kind: "ArtifactSectionKind"

    model_config = BaseEntity.model_config | {"arbitrary_types_allowed": True}

    def cells_meta(self) -> dict[str, Any]:
        return {"section_kind": repr(self.section_kind)}


class ArtifactSection(BaseEntity):
    # some section may have no id and kind — it is ok for simple text sections
    id: ArtifactLocalId | None
    kind: FullArtifactLocalId | None
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

    def validate(self) -> tuple[bool, list[Cell]]:  # type: ignore[override]
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

        primary_section = primary_sections[0]
        if primary_section.kind is None:
            return False, [
                Cell.build_meta(
                    kind="artifact_kind_validation",
                    id=str(self.id),
                    status="failure",
                    message="Primary section is missing a kind.",
                )
            ]

        section = resolve(primary_section.kind)
        if not isinstance(section.meta, ArtifactSectionKindMeta):
            return False, [
                Cell.build_meta(
                    kind="artifact_kind_validation",
                    id=str(self.id),
                    status="failure",
                    message=f"Primary section kind '{primary_section.kind}' is not available.",
                )
            ]

        primary_section_kind = section.meta.section_kind
        return primary_section_kind.validate_artifact(self)

    # TODO: should we attach section cells here as well?
    def cells(self) -> list[Cell]:
        primary_section = self.primary_section()
        cells = [
            Cell.build_meta(
                kind="artifact_meta",
                artifact_id=str(self.id),
                artifact_kind=str(primary_section.kind) if primary_section.kind else None,
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


class MarkdownSectionMixin:
    config_class: ClassVar[type[ArtifactSectionConfig]]

    def get_primary_section_id(
        self,
        artifact_id: FullArtifactId,
        source: "markdown.SectionSource",
        primary: bool = False,
    ) -> ArtifactLocalId | None:
        return ArtifactLocalId("markdown" + uuid.uuid4().hex.replace("-", ""))

    def markdown_build_title(
        self,
        artifact_id: FullArtifactId,
        source: "markdown.SectionSource",
        section_config: ArtifactSectionConfig,
        primary: bool = False,
    ) -> str:
        return source.title or ""

    def markdown_build_description(
        self,
        artifact_id: FullArtifactId,
        source: "markdown.SectionSource",
        section_config: ArtifactSectionConfig,
        primary: bool = False,
    ) -> str:
        return source.as_original_markdown(with_title=False)

    def markdown_construct_meta(
        self,
        artifact_id: FullArtifactId,
        source: "markdown.SectionSource",
        section_config: ArtifactSectionConfig,
        description: str,
        primary: bool = False,
    ) -> ArtifactSectionMeta:
        return ArtifactSectionMeta()

    def markdown_prepare_config(  # noqa: CCR001
        self,
        artifact_id: FullArtifactId,
        source: "markdown.SectionSource",
        config: dict[str, Any],
        primary: bool,
    ) -> dict[str, Any]:
        data = dict(config)

        if "id" not in data or data["id"] is None:
            data["id"] = self.get_primary_section_id(
                artifact_id=artifact_id,
                source=source,
                primary=primary,
            )

        if "kind" not in data or data["kind"] is None:
            if primary:
                raise NotImplementedError(f"Primary section for artifact '{artifact_id}' is missing a valid kind")
            raise NotImplementedError(f"Section for artifact '{artifact_id}' is missing a valid kind")

        raw_id = data.get("id")
        if isinstance(raw_id, str):
            data["id"] = ArtifactLocalId(raw_id)
        elif raw_id is None or isinstance(raw_id, ArtifactLocalId):
            pass
        else:
            raise NotImplementedError(f"Invalid section id for artifact '{artifact_id}': {raw_id!r}")

        kind_value = data.get("kind")
        if isinstance(kind_value, str):
            data["kind"] = FullArtifactLocalId.parse(kind_value)
        elif isinstance(kind_value, FullArtifactLocalId):
            pass
        else:
            raise NotImplementedError(f"Invalid section kind for artifact '{artifact_id}': {kind_value!r}")

        return data

    def markdown_construct_section(  # noqa: CCR001
        self,
        artifact_id: FullArtifactId,
        source: "markdown.SectionSource",
        config: dict[str, Any],
        primary: bool = False,
    ) -> ArtifactSection:
        data = self.markdown_prepare_config(artifact_id=artifact_id, source=source, config=config, primary=primary)

        section_config = self.config_class.parse_obj(data)

        title = self.markdown_build_title(
            artifact_id=artifact_id,
            source=source,
            section_config=section_config,
            primary=primary,
        )
        description = self.markdown_build_description(
            artifact_id=artifact_id,
            source=source,
            section_config=section_config,
            primary=primary,
        )
        meta = self.markdown_construct_meta(
            artifact_id=artifact_id,
            source=source,
            section_config=section_config,
            description=description,
            primary=primary,
        )

        return ArtifactSection(
            id=section_config.id,
            kind=section_config.kind,
            title=title,
            description=description,
            primary=primary,
            meta=meta,
        )


class ArtifactSectionKind(MarkdownSectionMixin, BaseEntity):
    config_class: ClassVar[type[ArtifactSectionConfig]] = ArtifactSectionConfig

    def execute_section(self, task: Task, unit: WorkUnit, section: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("You MUST implement this method.")

    def validate_artifact(self, artifact: "Artifact") -> tuple[bool, list[Cell]]:
        return True, [
            Cell.build_meta(
                kind="artifact_kind_validation",
                id=str(artifact.id),
                status="success",
            )
        ]


class ArtifactPrimarySectionKind(ArtifactSectionKind):
    def execute_section(self, task: Task, unit: WorkUnit, section: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("Primary sections cannot be executed.")

    def markdown_build_title(
        self,
        artifact_id: FullArtifactId,
        source: "markdown.SectionSource",
        section_config: ArtifactSectionConfig,
        primary: bool = False,
    ) -> str:
        return source.title or str(artifact_id)


def resolve(target_id: FullArtifactLocalId) -> ArtifactSection:
    from donna.world import artifacts as world_artifacts

    artifact = world_artifacts.load_artifact(target_id.full_artifact_id)
    section = artifact.get_section(target_id.local_id)

    if section is None:
        raise NotImplementedError(f"Section '{target_id}' is not available")

    return section
