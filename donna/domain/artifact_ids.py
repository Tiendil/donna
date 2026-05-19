from __future__ import annotations

from typing import NewType

from donna.domain.constants import DONNA_ARTIFACT_EXTENSION
from donna.domain.ids import SectionId
from donna.domain.paths import raw_project_path, validate_project_path_id

ArtifactId = NewType("ArtifactId", str)
ArtifactSectionId = NewType("ArtifactSectionId", str)

ARTIFACT_SECTION_DELIMITER = ":"


class ArtifactSectionParts:
    __slots__ = ("artifact_id", "full_id", "section_id")

    full_id: ArtifactSectionId
    artifact_id: ArtifactId
    section_id: SectionId

    def __init__(self, *, full_id: ArtifactSectionId, artifact_id: ArtifactId, section_id: SectionId) -> None:
        self.full_id = full_id
        self.artifact_id = artifact_id
        self.section_id = section_id


def validate_artifact_id(value: object) -> bool:
    if not validate_project_path_id(value):
        return False

    return value.lower().endswith(DONNA_ARTIFACT_EXTENSION)  # type: ignore[attr-defined, no-any-return]


def validate_artifact_section_id(value: object) -> bool:
    parts = split_artifact_section_id(value)
    return parts is not None


def artifact_path_parts(artifact_id: ArtifactId) -> tuple[str, ...]:
    raw = raw_project_path(artifact_id)
    if raw is None or not validate_artifact_id(artifact_id):
        raise ValueError(f"Invalid ArtifactId: {artifact_id}")

    return tuple(raw.split("/"))


def artifact_section_id(artifact_id: ArtifactId, local_id: SectionId | str) -> ArtifactSectionId:
    local_id = SectionId(local_id)
    section_id = f"{artifact_id}{ARTIFACT_SECTION_DELIMITER}{local_id}"

    if not validate_artifact_section_id(section_id):
        raise ValueError(f"Invalid ArtifactSectionId: {section_id}")

    return ArtifactSectionId(section_id)


def split_artifact_section_id(value: object) -> ArtifactSectionParts | None:
    if not isinstance(value, str) or not value:
        return None

    try:
        artifact_part, local_part = value.rsplit(ARTIFACT_SECTION_DELIMITER, maxsplit=1)
    except ValueError:
        return None

    if not validate_artifact_id(artifact_part) or not SectionId.validate(local_part):
        return None

    full_id = ArtifactSectionId(value)
    artifact_id = ArtifactId(artifact_part)

    return ArtifactSectionParts(
        full_id=full_id,
        artifact_id=artifact_id,
        section_id=SectionId(local_part),
    )
