from types import ModuleType

from donna.domain.ids import FullArtifactId, FullArtifactLocalId
from donna.machine.artifacts import Artifact, ArtifactMeta, ArtifactSection, ArtifactSectionKindMeta, resolve


def construct_artifact_from_module(module: ModuleType, full_id: FullArtifactId) -> Artifact:  # noqa: CCR001
    sections: list[ArtifactSection] = []

    for name, value in sorted(module.__dict__.items()):
        if not name.isidentifier():
            continue

        if name.startswith("_"):
            continue

        if isinstance(value, ArtifactSection):
            if value.id is None or value.kind is None:
                raise NotImplementedError(f"Module `{module.__name__}` defines section '{name}' without id/kind.")
            sections.append(value)

    primary_sections = [section for section in sections if section.primary]
    if len(primary_sections) != 1:
        raise NotImplementedError(
            f"Module `{module.__name__}` must define exactly one primary section, found {len(primary_sections)}."
        )

    primary_section = primary_sections[0]
    if primary_section.kind is None:
        raise NotImplementedError(f"Module `{module.__name__}` defines a primary section without a kind.")

    if isinstance(primary_section.kind, str):
        primary_kind = FullArtifactLocalId.parse(primary_section.kind)
        primary_section.kind = primary_kind

    expected_kind_id = FullArtifactLocalId.parse("donna.artifacts.python")
    if primary_section.kind != expected_kind_id:
        raise NotImplementedError(
            f"Primary section kind mismatch: module uses '{primary_section.kind}', but expected '{expected_kind_id}'."
        )

    if primary_section.kind.full_artifact_id == full_id:
        meta = ArtifactMeta()
    else:
        kind_section = resolve(primary_section.kind)
        if not isinstance(kind_section.meta, ArtifactSectionKindMeta):
            raise NotImplementedError(f"Primary section kind '{primary_section.kind}' is not available")
        primary_section_kind = kind_section.meta.section_kind
        meta = primary_section_kind.build_artifact_meta(full_id, sections)

    return Artifact(
        id=full_id,
        meta=meta,
        sections=sections,
    )
