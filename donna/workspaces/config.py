from __future__ import annotations

from typing import Literal

import pydantic
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


def _serialize_workflow_dir(path: RelativeProjectPath) -> str:
    return f"./{path.as_posix()}"


def _validate_relative_project_path(path: RelativeProjectPath) -> RelativeProjectPath:
    if path.is_absolute():
        raise ValueError("Project paths must be relative to the Donna project root.")

    if any(part == ".." for part in path.parts):
        raise ValueError("Project paths must not contain parent-directory references.")

    return RelativeProjectPath(path)


class Config(BaseEntity):
    version: Literal[1] = 1
    session_dir: RelativeProjectPath = RelativeProjectPath(DONNA_DEFAULT_SESSION_DIR)
    defaults: DefaultsConfig = pydantic.Field(default_factory=DefaultsConfig)
    workflow_dirs: list[RelativeProjectPath] = pydantic.Field(default_factory=_default_workflow_dirs)
    journal: JournalConfig = pydantic.Field(default_factory=JournalConfig)

    @pydantic.field_validator("session_dir", mode="after")
    @classmethod
    def validate_session_dir(cls, value: RelativeProjectPath) -> RelativeProjectPath:
        return _validate_relative_project_path(value)

    @pydantic.field_validator("workflow_dirs", mode="after")
    @classmethod
    def validate_workflow_dirs(cls, value: list[RelativeProjectPath]) -> list[RelativeProjectPath]:
        workflow_dirs: list[RelativeProjectPath] = []

        for path in value:
            path = _validate_relative_project_path(path)
            if path in workflow_dirs:
                continue

            workflow_dirs.append(path)

        return workflow_dirs

    @pydantic.field_serializer("workflow_dirs")
    def serialize_workflow_dirs(self, value: list[RelativeProjectPath]) -> list[str]:
        return [_serialize_workflow_dir(path) for path in value]


config = ContextValue[Config]("donna_config")
