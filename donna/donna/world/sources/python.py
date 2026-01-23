from types import ModuleType

from donna.domain.ids import FullArtifactId, FullArtifactLocalId
from donna.machine.artifacts import (
    Artifact,
    ArtifactKind,
    ArtifactKindSectionMeta,
    ArtifactMeta,
    ArtifactSection,
    ArtifactSectionKind,
    ArtifactSectionKindMeta,
    Section,
    resolve,
)
from donna.machine.templates import DirectiveConfig, DirectiveKind, DirectiveSectionMeta


def _resolve_section_kind(
    section_kind_id: FullArtifactLocalId,
    section_id: FullArtifactLocalId,
    section_kind_overrides: dict[FullArtifactLocalId, ArtifactSectionKind],
) -> ArtifactSectionKind:
    override = section_kind_overrides.get(section_id) or section_kind_overrides.get(section_kind_id)
    if override is not None:
        return override

    resolved_section = resolve(section_kind_id)
    if not isinstance(resolved_section.meta, ArtifactSectionKindMeta):
        raise NotImplementedError(f"Section kind '{section_kind_id}' is not available")
    return resolved_section.meta.section_kind


def _apply_section_entity_meta(section: ArtifactSection, section_def: Section) -> ArtifactSection:
    if section_def.entity is None:
        return section

    if isinstance(section_def.entity, DirectiveKind):
        directive_config = DirectiveConfig.model_validate(section_def.config.model_dump(mode="python"))
        return section.replace(
            meta=DirectiveSectionMeta(
                analyze_id=directive_config.analyze_id,
                directive=section_def.entity,
            )
        )

    if isinstance(section_def.entity, ArtifactKind):
        return section.replace(meta=ArtifactKindSectionMeta(artifact_kind=section_def.entity))

    if isinstance(section_def.entity, ArtifactSectionKind):
        return section.replace(meta=ArtifactSectionKindMeta(section_kind=section_def.entity))

    raise NotImplementedError(f"Unsupported section entity type: {type(section_def.entity).__name__}")


def construct_artifact_from_module(module: ModuleType, full_id: FullArtifactId) -> Artifact:  # noqa: CCR001
    title = getattr(module, "artifact_title", None)
    description = getattr(module, "artifact_description", None)
    artifact_kind = getattr(module, "artifact_kind", None)

    if title is None or description is None or artifact_kind is None:
        raise NotImplementedError(
            f"Module `{module.__name__}` is missing artifact metadata: "
            "artifact_title, artifact_description, artifact_kind."
        )

    if isinstance(artifact_kind, str):
        artifact_kind = FullArtifactLocalId.parse(artifact_kind)

    if not isinstance(artifact_kind, FullArtifactLocalId):
        raise NotImplementedError(f"Module `{module.__name__}` has invalid artifact_kind: '{artifact_kind}'.")

    expected_kind_id = FullArtifactLocalId.parse("donna.artifacts.python")
    if artifact_kind != expected_kind_id:
        raise NotImplementedError(
            f"Artifact kind mismatch: module uses '{artifact_kind}', but expected '{expected_kind_id}'."
        )

    section_defs: list[Section] = []
    section_kind_overrides: dict[FullArtifactLocalId, ArtifactSectionKind] = {}

    for name, value in sorted(module.__dict__.items()):
        if not name.isidentifier():
            continue

        if name.startswith("_"):
            continue

        if isinstance(value, Section):
            section_defs.append(value)

            if value.entity is not None and isinstance(value.entity, ArtifactSectionKind):
                section_id = full_id.to_full_local(value.config.id)
                section_kind_overrides[section_id] = value.entity

    sections: list[ArtifactSection] = []

    for section_def in section_defs:
        section_kind_id = section_def.config.kind
        section_id = full_id.to_full_local(section_def.config.id)
        section_kind = _resolve_section_kind(section_kind_id, section_id, section_kind_overrides)

        section = section_kind.from_python_section(
            artifact_id=full_id,
            module=module,
            section=section_def,
        )
        sections.append(_apply_section_entity_meta(section, section_def))

    return Artifact(
        id=full_id,
        kind=artifact_kind,
        title=title,
        description=description,
        meta=ArtifactMeta(),
        sections=sections,
    )
