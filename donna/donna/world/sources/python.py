from types import ModuleType

from donna.domain.ids import FullArtifactId, FullArtifactLocalId
from donna.machine.artifacts import Artifact, ArtifactMeta, ArtifactSection


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

    return Artifact(
        id=full_id,
        kind=artifact_kind,
        title=title,
        description=description,
        meta=ArtifactMeta(),
        sections=sections,
    )
