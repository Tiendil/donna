from __future__ import annotations

from pathlib import Path
from typing import NewType

from donna.domain.constants import ARTIFACT_ID_PREFIX

ProjectRootPath = NewType("ProjectRootPath", Path)
ProjectPathId = NewType("ProjectPathId", str)
ProjectPathRaw = NewType("ProjectPathRaw", str)
ProjectConfigPath = NewType("ProjectConfigPath", Path)
RelativeProjectPath = NewType("RelativeProjectPath", Path)
ResolvedProjectPath = NewType("ResolvedProjectPath", Path)
UntrustedPath = NewType("UntrustedPath", Path)
PathInput = Path | UntrustedPath | ProjectRootPath | ProjectConfigPath


def raw_project_path(value: object) -> ProjectPathRaw | None:
    if not isinstance(value, str) or not value.startswith(ARTIFACT_ID_PREFIX):
        return None

    raw = value.removeprefix(ARTIFACT_ID_PREFIX)
    if not raw:
        return None

    return ProjectPathRaw(raw)


def validate_project_path_id(value: object) -> bool:
    raw = raw_project_path(value)
    if raw is None:
        return False

    parts = tuple(raw.split("/"))
    if any(part in ("", ".", "..") for part in parts):
        return False

    return True
