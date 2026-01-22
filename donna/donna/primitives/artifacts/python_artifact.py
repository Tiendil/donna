import types

from donna.domain.ids import FullArtifactId, FullArtifactLocalId
from donna.machine.artifacts import (
    Artifact,
    ArtifactConstructor,
    ArtifactContent,
    ArtifactKind,
    ArtifactMeta,
    ArtifactSection,
    ArtifactSectionKind,
    SectionConstructor,
)


class PythonArtifact(ArtifactKind):
    def construct_artifact(self, source: ArtifactContent) -> Artifact:
        raise NotImplementedError("Python artifacts are constructed from modules, not markdown sources.")

    def construct_module_artifact(  # noqa: CCR001
        self,
        module: types.ModuleType,
        artifact_id: FullArtifactId,
        kind_id: FullArtifactLocalId,
    ) -> Artifact | None:
        artifact_constructor: ArtifactConstructor | None = None

        for value in module.__dict__.values():
            if isinstance(value, ArtifactConstructor):
                if artifact_constructor is not None:
                    raise NotImplementedError("Artifact module must define only one ArtifactConstructor.")

                artifact_constructor = value

        if artifact_constructor is None:
            return None

        title = artifact_constructor.title
        description = artifact_constructor.description
        artifact_kind_id = artifact_constructor.config.kind

        if artifact_kind_id != kind_id:
            raise NotImplementedError(
                f"Artifact kind mismatch: constructor uses '{artifact_kind_id}', but expected '{kind_id}'."
            )

        sections: list[ArtifactSection] = []

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
                    section_id = artifact_id.to_full_local(value.config.id)
                    section_kind_overrides[section_id] = value.entity

        for constructor in constructors:
            section = constructor.build_section(
                artifact_kind=self,
                artifact_id=artifact_id,
                section_kind_overrides=section_kind_overrides,
            )
            sections.append(section)

        return Artifact(
            id=artifact_id,
            kind=artifact_kind_id,
            title=title,
            description=description,
            meta=ArtifactMeta(),
            sections=sections,
        )
