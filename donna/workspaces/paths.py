from __future__ import annotations

import pathlib

from llm_tool_cli.core.result import Err, Ok, Result, unwrap_to_error
from llm_tool_cli.paths import (
    ProjectPathId,
    ProjectRootPath,
    ResolvedProjectPath,
    normalize_project_path_id,
    resolve_inside_project,
    resolve_project_root,
    resolve_root_anchored_path,
)
from llm_tool_cli.paths.errors import InvalidProjectPath

from donna.domain import errors as domain_errors
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
from donna.domain.paths import PathInput, UntrustedPath

PROJECT_ROOT_PREFIX = ARTIFACT_ID_PREFIX


def _canonical_from_resolved(resolved: ResolvedProjectPath, root: ProjectRootPath) -> Result[ProjectPathId]:
    return normalize_project_path_id(
        PROJECT_ROOT_PREFIX + pathlib.Path(resolved).relative_to(pathlib.Path(root)).as_posix()
    )


@unwrap_to_error
def resolve_project_path(value: str, root: PathInput, *, allow_absolute: bool = True) -> Result[ResolvedProjectPath]:
    project_root = resolve_project_root(root).unwrap()

    if value.startswith("@"):
        return resolve_root_anchored_path(value, project_root)

    path = pathlib.Path(value).expanduser()

    if path.is_absolute() and not allow_absolute:
        return Err([InvalidProjectPath(path=value)])

    candidate = path if path.is_absolute() else pathlib.Path(project_root) / path
    return resolve_inside_project(candidate, project_root)


@unwrap_to_error
def normalize_path(value: str, root: PathInput, *, cwd: PathInput | None = None) -> Result[ProjectPathId]:
    project_root = resolve_project_root(root).unwrap()

    if value.startswith("@"):
        return normalize_project_path_id(value)

    path = pathlib.Path(value).expanduser()
    candidate = path if path.is_absolute() else pathlib.Path(cwd or project_root) / path
    resolved = resolve_inside_project(candidate, project_root).unwrap()

    return _canonical_from_resolved(resolved, project_root)


@unwrap_to_error
def normalize_existing_path(path: UntrustedPath, root: PathInput) -> Result[ProjectPathId]:
    project_root = resolve_project_root(root).unwrap()
    resolved = resolve_inside_project(path, project_root).unwrap()

    return _canonical_from_resolved(resolved, project_root)


def normalize_project_path(
    value: str,
    root: PathInput,
    *,
    cwd: PathInput | None = None,
    relative_to: ArtifactId | None = None,
) -> Result[ProjectPathId]:
    if not isinstance(value, str) or not value:
        return Err([InvalidProjectPath(path=str(value))])

    if relative_to is None:
        return normalize_path(value, root, cwd=cwd)

    path = pathlib.Path(value).expanduser()
    if value.startswith(PROJECT_ROOT_PREFIX) or path.is_absolute():
        return normalize_path(value, root, cwd=cwd)

    parent_parts = artifact_path_parts(relative_to)[:-1]
    return normalize_project_path_id(PROJECT_ROOT_PREFIX + "/".join((*parent_parts, value)))


@unwrap_to_error
def normalize_artifact_id(
    value: str,
    root: PathInput,
    *,
    cwd: PathInput | None = None,
    relative_to: ArtifactId | None = None,
) -> Result[ArtifactId]:
    normalized = normalize_project_path(value, root, cwd=cwd, relative_to=relative_to).unwrap()

    if not validate_artifact_id(normalized):
        return Err([domain_errors.InvalidIdFormat(id_type=ArtifactId.__name__, value=value)])

    return Ok(ArtifactId(normalized))


@unwrap_to_error
def normalize_artifact_section_id(
    value: str,
    root: PathInput,
    *,
    cwd: PathInput | None = None,
    relative_to: ArtifactId | None = None,
) -> Result[ArtifactSectionId]:
    if not isinstance(value, str) or not value:
        return Err([domain_errors.InvalidIdFormat(id_type=f"{ArtifactSectionId.__name__} format", value=str(value))])

    try:
        artifact_part, local_part = value.rsplit(ARTIFACT_SECTION_DELIMITER, maxsplit=1)
    except ValueError:
        return Err([domain_errors.InvalidIdFormat(id_type=f"{ArtifactSectionId.__name__} format", value=value)])

    normalized = normalize_project_path(artifact_part, root, cwd=cwd, relative_to=relative_to).unwrap()
    if not validate_artifact_id(normalized) or not SectionId.validate(local_part):
        return Err([domain_errors.InvalidIdFormat(id_type=f"{ArtifactSectionId.__name__} format", value=value)])

    return Ok(artifact_section_id(ArtifactId(normalized), SectionId(local_part)))
