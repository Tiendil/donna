from __future__ import annotations

import pathlib
from typing import NewType

from donna.domain.constants import ARTIFACT_ID_PREFIX
from donna.domain.ids import SectionId, _is_artifact_slug_part

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


def _raw_artifact_path(value: object) -> str | None:
    if not isinstance(value, str) or not value.startswith(ARTIFACT_ID_PREFIX):
        return None

    raw = value.removeprefix(ARTIFACT_ID_PREFIX)
    if not raw:
        return None

    return raw


def validate_artifact_id(value: object) -> bool:
    raw = _raw_artifact_path(value)
    if raw is None:
        return False

    parts = tuple(raw.split("/"))
    if any(part == "" for part in parts):
        return False

    if not all(_is_artifact_slug_part(part) for part in parts):
        return False

    return bool(pathlib.PurePosixPath(parts[-1]).suffix)


def validate_artifact_section_id(value: object) -> bool:
    parts = split_artifact_section_id(value)
    return parts is not None


def artifact_path_parts(artifact_id: ArtifactId) -> tuple[str, ...]:
    raw = _raw_artifact_path(str(artifact_id))
    if raw is None or not validate_artifact_id(str(artifact_id)):
        raise ValueError(f"Invalid ArtifactId: {artifact_id}")

    return tuple(raw.split("/"))


def artifact_section_id(artifact_id: ArtifactId, local_id: SectionId | str) -> ArtifactSectionId:
    local_id = SectionId(str(local_id))
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
