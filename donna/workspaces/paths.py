from __future__ import annotations

import pathlib

from donna.domain.artifact_ids import (
    ARTIFACT_SECTION_DELIMITER,
    ArtifactId,
    ArtifactSectionId,
    artifact_path_parts,
    artifact_section_id,
    validate_artifact_id,
)
from donna.domain.constants import ARTIFACT_ID_PREFIX
from donna.domain.ids import SectionId
from donna.domain.paths import PathInput, ProjectPathId, ProjectRootPath, ResolvedProjectPath, UntrustedPath

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


def _normalize_parts(raw: str, *, initial_parts: tuple[str, ...] = ()) -> ProjectPathId | None:
    if not raw:
        return None

    parts = list(initial_parts)

    for part in raw.split("/"):
        if not _append_normalized_part(parts, part):
            return None

    if not parts:
        return None

    normalized = ProjectPathId(PROJECT_ROOT_PREFIX + "/".join(parts))
    if not validate_artifact_id(normalized):
        return None

    return normalized


def resolve_project_root(root: UntrustedPath) -> ProjectRootPath:
    return ProjectRootPath(root.resolve())


def _normalize_root_anchored(value: str) -> ProjectPathId | None:
    if not value.startswith(PROJECT_ROOT_PREFIX):
        return None

    return _normalize_parts(value.removeprefix(PROJECT_ROOT_PREFIX))


def _resolve_inside_project(path: UntrustedPath, root: ProjectRootPath) -> ResolvedProjectPath | None:
    resolved = path.resolve()
    root_path = pathlib.Path(root)

    if resolved == root_path or not resolved.is_relative_to(root_path):
        return None

    return ResolvedProjectPath(resolved)


def _canonical_from_resolved(resolved: ResolvedProjectPath, root: ProjectRootPath) -> ProjectPathId | None:
    normalized = ProjectPathId(PROJECT_ROOT_PREFIX + pathlib.Path(resolved).relative_to(pathlib.Path(root)).as_posix())
    if not validate_artifact_id(normalized):
        return None

    return normalized


def _resolve_root_anchored_path(value: str, root: ProjectRootPath) -> ResolvedProjectPath | None:
    normalized = _normalize_root_anchored(value)
    if normalized is None:
        return None

    path = pathlib.Path(root).joinpath(*normalized.removeprefix(PROJECT_ROOT_PREFIX).split("/"))
    return _resolve_inside_project(UntrustedPath(path), root)


def resolve_project_path(value: str, root: PathInput, *, allow_absolute: bool = True) -> ResolvedProjectPath | None:
    project_root = ProjectRootPath(root.resolve())

    if value.startswith("@"):
        if not value.startswith(PROJECT_ROOT_PREFIX):
            return None
        return _resolve_root_anchored_path(value, project_root)

    path = pathlib.Path(value).expanduser()

    if path.is_absolute() and not allow_absolute:
        return None

    candidate = path if path.is_absolute() else pathlib.Path(project_root) / path
    return _resolve_inside_project(UntrustedPath(candidate), project_root)


def normalize_path(value: str, root: PathInput, *, cwd: PathInput | None = None) -> ProjectPathId | None:
    project_root = ProjectRootPath(root.resolve())

    if value.startswith("@"):
        return _normalize_root_anchored(value)

    path = pathlib.Path(value).expanduser()
    candidate = path if path.is_absolute() else pathlib.Path(cwd or project_root) / path
    resolved = _resolve_inside_project(UntrustedPath(candidate), project_root)

    if resolved is None:
        return None

    return _canonical_from_resolved(resolved, project_root)


def normalize_existing_path(path: UntrustedPath, root: PathInput) -> ProjectPathId | None:
    project_root = ProjectRootPath(root.resolve())
    resolved = _resolve_inside_project(path, project_root)

    if resolved is None:
        return None

    return _canonical_from_resolved(resolved, project_root)


def _normalize_from_artifact(value: str, relative_to: ArtifactId) -> ProjectPathId | None:
    if value.startswith(PROJECT_ROOT_PREFIX):
        return _normalize_root_anchored(value)

    return _normalize_parts(value, initial_parts=artifact_path_parts(relative_to)[:-1])


def normalize_artifact_path(
    value: str,
    root: PathInput,
    *,
    cwd: PathInput | None = None,
    relative_to: ArtifactId | None = None,
) -> ProjectPathId | None:
    if not isinstance(value, str) or not value:
        return None

    if relative_to is not None:
        return _normalize_from_artifact(value, relative_to)

    return normalize_path(value, root, cwd=cwd)


def normalize_artifact_id(
    value: str,
    root: PathInput,
    *,
    cwd: PathInput | None = None,
    relative_to: ArtifactId | None = None,
) -> ArtifactId | None:
    normalized = normalize_artifact_path(value, root, cwd=cwd, relative_to=relative_to)
    if normalized is None:
        return None

    return ArtifactId(normalized)


def normalize_artifact_section_id(
    value: str,
    root: PathInput,
    *,
    cwd: PathInput | None = None,
    relative_to: ArtifactId | None = None,
) -> ArtifactSectionId | None:
    if not isinstance(value, str) or not value:
        return None

    try:
        artifact_part, local_part = value.rsplit(ARTIFACT_SECTION_DELIMITER, maxsplit=1)
    except ValueError:
        return None

    artifact_id = normalize_artifact_id(artifact_part, root, cwd=cwd, relative_to=relative_to)
    if artifact_id is None or not SectionId.validate(local_part):
        return None

    return artifact_section_id(artifact_id, SectionId(local_part))
