from __future__ import annotations

import enum
import pathlib
from typing import TYPE_CHECKING

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.id_paths import NormalizedRawIdPath
from donna.domain.ids import SectionId
from donna.domain.python_path import PythonPath
from donna.workspaces import errors as world_errors

if TYPE_CHECKING:
    from donna.protocol.modes import Mode

DONNA_CONFIG_NAME = "donna.toml"
DONNA_DEFAULT_SESSION_DIR = pathlib.Path(".session") / "donna"
DONNA_DEFAULT_WORKFLOW_DIR = pathlib.Path("workflows")


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


def _default_workflow_dirs() -> list[pathlib.Path]:
    return [
        DONNA_DEFAULT_WORKFLOW_DIR,
        DONNA_DEFAULT_SESSION_DIR,
    ]


def _serialize_workflow_dir(path: pathlib.Path) -> str:
    return f"./{path.as_posix()}"


def _validate_workflow_dir(path: pathlib.Path) -> pathlib.Path:
    if path.is_absolute():
        raise ValueError("Workflow directories must be relative to the Donna project root.")

    if any(part == ".." for part in path.parts):
        raise ValueError("Workflow directories must not contain parent-directory references.")

    return path


class Config(BaseEntity):
    session: pathlib.Path = DONNA_DEFAULT_SESSION_DIR
    default_section_kind: PythonPath = PythonPath(NormalizedRawIdPath("donna.lib.text"))
    default_primary_section_kind: PythonPath = PythonPath(NormalizedRawIdPath("donna.lib.workflow"))
    default_primary_section_id: SectionId = SectionId("primary")
    workflow_dirs: list[pathlib.Path] = pydantic.Field(default_factory=_default_workflow_dirs)
    journal: JournalConfig = pydantic.Field(default_factory=JournalConfig)

    cache_lifetime: float = 1.0

    @pydantic.field_validator("workflow_dirs", mode="after")
    @classmethod
    def validate_workflow_dirs(cls, value: list[pathlib.Path]) -> list[pathlib.Path]:
        workflow_dirs: list[pathlib.Path] = []

        for path in value:
            path = _validate_workflow_dir(path)
            if path in workflow_dirs:
                continue

            workflow_dirs.append(path)

        return workflow_dirs

    @pydantic.field_serializer("workflow_dirs")
    def serialize_workflow_dirs(self, value: list[pathlib.Path]) -> list[str]:
        return [_serialize_workflow_dir(path) for path in value]


class Workspace(BaseEntity):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    root: pydantic.DirectoryPath
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


project_dir = GlobalConfig[pathlib.Path]()
config = GlobalConfig[Config]()
protocol: GlobalConfig["Mode"] = GlobalConfig()


def install_workspace(workspace: Workspace) -> None:
    if not project_dir.is_set():
        project_dir.set(pathlib.Path(workspace.root))

    if not config.is_set():
        config.set(workspace.config)
