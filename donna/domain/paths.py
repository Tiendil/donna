from __future__ import annotations

from pathlib import Path
from typing import NewType

from llm_tool_cli.paths import ProjectRootPath

from donna.domain.constants import ARTIFACT_ID_PREFIX

ProjectPathRaw = NewType("ProjectPathRaw", str)
ProjectConfigPath = NewType("ProjectConfigPath", Path)
RelativeProjectPath = NewType("RelativeProjectPath", Path)
UntrustedPath = NewType("UntrustedPath", Path)
PathInput = Path | UntrustedPath | ProjectRootPath | ProjectConfigPath


def raw_project_path(value: object) -> ProjectPathRaw | None:
    if not isinstance(value, str) or not value.startswith(ARTIFACT_ID_PREFIX):
        return None

    raw = value.removeprefix(ARTIFACT_ID_PREFIX)
    if not raw:
        return None

    return ProjectPathRaw(raw)
