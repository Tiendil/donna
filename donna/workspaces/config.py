from __future__ import annotations

import enum
from typing import TYPE_CHECKING

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.constants import DONNA_DEFAULT_SESSION_DIR, DONNA_DEFAULT_WORKFLOW_DIR
from donna.domain.id_paths import NormalizedRawIdPath
from donna.domain.ids import SectionId
from donna.domain.paths import ProjectRootPath, RelativeProjectPath
from donna.domain.python_path import PythonPath
from donna.workspaces import errors as world_errors

if TYPE_CHECKING:
    from donna.protocol.modes import Mode


class JournalRecordAttribute(str, enum.Enum):
    timestamp = "timestamp"
    actor_id = "actor_id"
    message = "message"
    current_task_id = "current_task_id"
    current_work_unit_id = "current_work_unit_id"
    current_operation_id = "current_operation_id"

    @classmethod
    def has_attribute(cls, name: str) -> bool:
        return name in cls.__members__


def _is_journal_variable_argument(argument: str) -> bool:
    return len(argument) >= 2 and argument[0] == "{" and argument[-1] == "}"


class JournalConfig(BaseEntity):
    cmd: list[str] | None = None

    @pydantic.field_validator("cmd", mode="after")
    @classmethod
    def validate_cmd(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value

        if not value:
            raise ValueError("Journal command config is invalid: Configured command is empty.")

        for argument in value:
            if not _is_journal_variable_argument(argument):
                continue

            name = argument[1:-1]

            if not JournalRecordAttribute.has_attribute(name):
                raise ValueError(
                    f"Journal command config is invalid: `{name}` is not a supported `JournalRecord` argument."
                )

        return value


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
    session_dir: RelativeProjectPath = RelativeProjectPath(DONNA_DEFAULT_SESSION_DIR)
    default_section_kind: PythonPath = PythonPath(NormalizedRawIdPath("donna.lib.text"))
    default_primary_section_kind: PythonPath = PythonPath(NormalizedRawIdPath("donna.lib.workflow"))
    default_primary_section_id: SectionId = SectionId("primary")
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


class Workspace(BaseEntity):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    root: ProjectRootPath
    config: Config


class GlobalConfig[V]():
    __slots__ = ("_value",)

    def __init__(self) -> None:
        self._value: V | None = None

    def set(self, value: V) -> None:
        if self._value is not None:
            raise world_errors.GlobalConfigAlreadySet()

        self._value = value

    def get(self) -> V:
        if self._value is None:
            raise world_errors.GlobalConfigNotSet()

        return self._value

    def is_set(self) -> bool:
        return self._value is not None

    def __call__(self) -> V:
        return self.get()


project_dir = GlobalConfig[ProjectRootPath]()
config = GlobalConfig[Config]()
protocol: GlobalConfig["Mode"] = GlobalConfig()


def install_workspace(workspace: Workspace) -> None:
    if not project_dir.is_set():
        project_dir.set(ProjectRootPath(workspace.root))

    if not config.is_set():
        config.set(workspace.config)
