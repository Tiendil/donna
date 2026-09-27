from __future__ import annotations

from pathlib import Path
from typing import NewType

from llm_tool_cli.paths import ProjectRootPath

ProjectConfigPath = NewType("ProjectConfigPath", Path)
RelativeProjectPath = NewType("RelativeProjectPath", Path)
UntrustedPath = NewType("UntrustedPath", Path)
PathInput = Path | UntrustedPath | ProjectRootPath | ProjectConfigPath
