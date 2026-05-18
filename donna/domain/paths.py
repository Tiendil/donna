from __future__ import annotations

from pathlib import Path
from typing import NewType

ProjectRootPath = NewType("ProjectRootPath", Path)
ProjectPathId = NewType("ProjectPathId", str)
ProjectConfigPath = NewType("ProjectConfigPath", Path)
RelativeProjectPath = NewType("RelativeProjectPath", Path)
ResolvedProjectPath = NewType("ResolvedProjectPath", Path)
UntrustedPath = NewType("UntrustedPath", Path)
PathInput = Path | UntrustedPath | ProjectRootPath | ProjectConfigPath
