from __future__ import annotations

from typing import Literal

import pydantic
from llm_tool_cli.config.fields import ConfigVersion, SessionDir, validate_relative_project_path
from llm_tool_cli.core.context import ContextValue
from llm_tool_cli.core.entities import BaseEntity
from llm_tool_cli.output.journal import JournalConfig
from llm_tool_cli.paths import RelativeProjectPath

from donna.domain.constants import DONNA_DEFAULT_SESSION_DIR, DONNA_DEFAULT_WORKFLOW_DIR
from donna.domain.id_paths import NormalizedRawIdPath
from donna.domain.ids import SectionId
from donna.domain.python_path import PythonPath


class DefaultsConfig(BaseEntity):
    tail_section_kind: PythonPath = PythonPath(NormalizedRawIdPath("donna.lib.text"))
    primary_section_kind: PythonPath = PythonPath(NormalizedRawIdPath("donna.lib.workflow"))
    primary_section_id: SectionId = SectionId("primary")


def _default_workflow_dirs() -> list[RelativeProjectPath]:
    return [
        RelativeProjectPath(DONNA_DEFAULT_WORKFLOW_DIR),
        RelativeProjectPath(DONNA_DEFAULT_SESSION_DIR),
    ]


class Config(BaseEntity):
    version: ConfigVersion[Literal[1]] = 1
    session_dir: SessionDir = RelativeProjectPath(DONNA_DEFAULT_SESSION_DIR)
    defaults: DefaultsConfig = pydantic.Field(default_factory=DefaultsConfig)
    workflow_dirs: list[RelativeProjectPath] = pydantic.Field(default_factory=_default_workflow_dirs)
    template_dirs: list[RelativeProjectPath] = pydantic.Field(default_factory=list)
    journal: JournalConfig = pydantic.Field(default_factory=JournalConfig)

    @pydantic.field_validator("workflow_dirs", "template_dirs", mode="after")
    @classmethod
    def validate_project_dirs(cls, value: list[RelativeProjectPath]) -> list[RelativeProjectPath]:
        return list(dict.fromkeys(validate_relative_project_path(path) for path in value))

    @pydantic.field_serializer("workflow_dirs", "template_dirs")
    def serialize_project_dirs(self, value: list[RelativeProjectPath]) -> list[str]:
        return [f"./{path.as_posix()}" for path in value]


config = ContextValue[Config]("donna_config")
