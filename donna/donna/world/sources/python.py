from types import ModuleType
from typing import Protocol

from donna.domain.ids import FullArtifactId, FullArtifactLocalId
from donna.machine.artifacts import (
    Artifact,
    ArtifactConstructor,
    ArtifactMeta,
    ArtifactSection,
    ArtifactSectionKind,
    SectionConstructor,
)


class PythonSectionConstructor(Protocol):
    def from_python_section(
        self,
        artifact_id: FullArtifactId,
        module: ModuleType,
        section: SectionConstructor,
    ) -> ArtifactSection:
        ...


def construct_artifact_from_module(module: ModuleType, full_id: FullArtifactId) -> Artifact:  # noqa: CCR001
    artifact_constructor: ArtifactConstructor | None = None

    for value in module.__dict__.values():
        if isinstance(value, ArtifactConstructor):
            if artifact_constructor is not None:
                raise NotImplementedError("Artifact module must define only one ArtifactConstructor.")

            artifact_constructor = value

    if artifact_constructor is None:
        raise NotImplementedError(f"Module `{module.__name__}` is not an artifact")

    title = artifact_constructor.title
    description = artifact_constructor.description
    artifact_kind_id = artifact_constructor.config.kind
    expected_kind_id = FullArtifactLocalId.parse("donna.artifacts.python")

    if artifact_kind_id != expected_kind_id:
        raise NotImplementedError(
            f"Artifact kind mismatch: constructor uses '{artifact_kind_id}', but expected '{expected_kind_id}'."
        )

    constructors: list[SectionConstructor] = []
    section_kind_overrides: dict[FullArtifactLocalId, ArtifactSectionKind] = {}

    for name, value in sorted(module.__dict__.items()):
        if not name.isidentifier():
            continue

        if name.startswith("_"):
            continue

        if isinstance(value, SectionConstructor):
            constructors.append(value)

            if value.entity is not None and isinstance(value.entity, ArtifactSectionKind):
                section_id = full_id.to_full_local(value.config.id)
                section_kind_overrides[section_id] = value.entity

    sections: list[ArtifactSection] = [
        constructor.build_section(
            artifact_id=full_id,
            module=module,
            section_kind_overrides=section_kind_overrides,
        )
        for constructor in constructors
    ]

    return Artifact(
        id=full_id,
        kind=artifact_kind_id,
        title=title,
        description=description,
        meta=ArtifactMeta(),
        sections=sections,
    )
