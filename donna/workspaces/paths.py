from __future__ import annotations

import pathlib

from donna.domain.artifact_ids import ArtifactId, ArtifactSectionId
from donna.domain.constants import ARTIFACT_ID_PREFIX
from donna.domain.id_paths import NormalizedRawIdPath
from donna.domain.ids import SectionId

PROJECT_ROOT_PREFIX = ARTIFACT_ID_PREFIX


def _append_normalized_part(parts: list[str], part: str) -> bool:
    if part == "":
        return False

    if part == ".":
        return True

    if part == "..":
        if not parts:
            return False
        parts.pop()
        return True

    parts.append(part)
    return True


def _normalize_parts(raw: str, *, initial_parts: tuple[str, ...] = ()) -> NormalizedRawIdPath | None:
    if not raw:
        return None

    parts = list(initial_parts)

    for part in raw.split("/"):
        if not _append_normalized_part(parts, part):
            return None

    if not parts:
        return None

    normalized = NormalizedRawIdPath("/".join(parts))
    if not ArtifactId.validate(normalized):
        return None

    return normalized


def _normalize_root_anchored(value: str) -> NormalizedRawIdPath | None:
    if not value.startswith(PROJECT_ROOT_PREFIX):
        return None

    return _normalize_parts(value.removeprefix(PROJECT_ROOT_PREFIX))


def _normalize_from_filesystem(
    value: str, root: pathlib.Path, *, cwd: pathlib.Path | None = None
) -> NormalizedRawIdPath | None:
    project_root = root.resolve()
    path = pathlib.Path(value).expanduser()

    if path.is_absolute():
        candidate = path
    else:
        candidate = (cwd or project_root) / path

    resolved = candidate.resolve()

    if resolved == project_root or not resolved.is_relative_to(project_root):
        return None

    normalized = NormalizedRawIdPath(resolved.relative_to(project_root).as_posix())
    if not ArtifactId.validate(normalized):
        return None

    return normalized


def _normalize_from_artifact(value: str, relative_to: ArtifactId) -> NormalizedRawIdPath | None:
    if value.startswith(PROJECT_ROOT_PREFIX):
        return _normalize_root_anchored(value)

    return _normalize_parts(value, initial_parts=relative_to.parts[:-1])


def normalize_artifact_path(
    value: str,
    root: pathlib.Path,
    *,
    cwd: pathlib.Path | None = None,
    relative_to: ArtifactId | None = None,
) -> NormalizedRawIdPath | None:
    if not isinstance(value, str) or not value:
        return None

    if relative_to is not None:
        return _normalize_from_artifact(value, relative_to)

    if value.startswith("@"):
        return _normalize_root_anchored(value)

    return _normalize_from_filesystem(value, root, cwd=cwd)


def normalize_artifact_id(
    value: str,
    root: pathlib.Path,
    *,
    cwd: pathlib.Path | None = None,
    relative_to: ArtifactId | None = None,
) -> ArtifactId | None:
    normalized = normalize_artifact_path(value, root, cwd=cwd, relative_to=relative_to)
    if normalized is None:
        return None

    return ArtifactId(normalized)


def normalize_artifact_section_id(
    value: str,
    root: pathlib.Path,
    *,
    cwd: pathlib.Path | None = None,
    relative_to: ArtifactId | None = None,
) -> ArtifactSectionId | None:
    if not isinstance(value, str) or not value:
        return None

    try:
        artifact_part, local_part = value.rsplit(ArtifactSectionId.delimiter, maxsplit=1)
    except ValueError:
        return None

    artifact_id = normalize_artifact_id(artifact_part, root, cwd=cwd, relative_to=relative_to)
    if artifact_id is None or not SectionId.validate(local_part):
        return None

    return ArtifactSectionId(NormalizedRawIdPath(f"{artifact_id.raw_value}{ArtifactSectionId.delimiter}{local_part}"))
