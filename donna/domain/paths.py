from __future__ import annotations

from pathlib import Path
from typing import NewType

from llm_tool_cli.paths import ProjectRootPath, UntrustedPath

ProjectConfigPath = NewType("ProjectConfigPath", Path)
RelativeProjectPath = NewType("RelativeProjectPath", Path)
PathInput = Path | UntrustedPath | ProjectRootPath | ProjectConfigPath
