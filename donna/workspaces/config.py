from __future__ import annotations

import enum
import pathlib
from typing import TYPE_CHECKING, Any

import pydantic

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.artifact_ids import ArtifactIdPattern
from donna.domain.python_path import PythonPath
from donna.machine.primitives import resolve_primitive
from donna.workspaces import errors as world_errors
from donna.workspaces.sources.base import SourceConfig as SourceConfigValue
from donna.workspaces.sources.base import SourceConstructor

if TYPE_CHECKING:
    from donna.protocol.modes import Mode

DONNA_CONFIG_NAME = "donna.toml"
DONNA_DEFAULT_SESSION_DIR = pathlib.Path(".session") / "donna"


class SourceConfig(BaseEntity):
    kind: PythonPath
    extension: str

    model_config = pydantic.ConfigDict(extra="allow")


class FileFilterMode(str, enum.Enum):
    ignore = "ignore"
    include = "include"
    required = "required"


class FileFilter(BaseEntity):
    mode: FileFilterMode
    pattern: ArtifactIdPattern


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


def _default_sources() -> list[SourceConfig]:
    return [
        SourceConfig.model_validate(
            {
                "kind": "donna.lib.sources.markdown",
                "extension": ".donna.md",
            }
        ),
    ]


def _default_file_filters() -> list[FileFilter]:
    return [
        FileFilter(mode=FileFilterMode.include, pattern=ArtifactIdPattern.parse("@/.agents/**/*.donna.md").unwrap()),
        FileFilter(mode=FileFilterMode.ignore, pattern=ArtifactIdPattern.parse(".*/**").unwrap()),
        FileFilter(mode=FileFilterMode.include, pattern=ArtifactIdPattern.parse("**/*.donna.md").unwrap()),
        FileFilter(mode=FileFilterMode.ignore, pattern=ArtifactIdPattern.parse("**").unwrap()),
    ]


class Config(BaseEntity):
    session: pathlib.Path = DONNA_DEFAULT_SESSION_DIR
    sources: list[SourceConfig] = pydantic.Field(default_factory=_default_sources)
    file_filters: list[FileFilter] = pydantic.Field(default_factory=_default_file_filters)
    journal: JournalConfig = pydantic.Field(default_factory=JournalConfig)
    _sources_instances: list[SourceConfigValue] = pydantic.PrivateAttr(default_factory=list)

    cache_lifetime: float = 1.0

    def model_post_init(self, __context: Any) -> None:  # noqa: CCR001
        sources: list[SourceConfigValue] = []

        for source_config in self.sources:
            primitive_result = resolve_primitive(source_config.kind)
            if primitive_result.is_err():
                error = primitive_result.unwrap_err()[0]
                raise ValueError(error.message.format(error=error))

            primitive = primitive_result.unwrap()

            if not isinstance(primitive, SourceConstructor):
                raise ValueError(f"Source constructor '{source_config.kind}' is not supported")

            sources.append(primitive.construct_source(source_config))

        object.__setattr__(self, "_sources_instances", sources)
        session_filter = FileFilter(mode=FileFilterMode.include, pattern=self.session_artifact_pattern())
        if session_filter not in self.file_filters:
            object.__setattr__(self, "file_filters", [session_filter, *self.file_filters])

    def session_artifact_pattern(self) -> ArtifactIdPattern:
        session_path = self.session.as_posix().strip("/")
        if session_path in {"", "."}:
            return ArtifactIdPattern.parse("@/**/*.donna.md").unwrap()

        return ArtifactIdPattern.parse(f"@/{session_path}/**/*.donna.md").unwrap()

    @property
    def sources_instances(self) -> list[SourceConfigValue]:
        return list(self._sources_instances)

    def get_source_config(self, kind: str) -> Result[SourceConfigValue, ErrorsList]:
        for source in self._sources_instances:
            if source.kind == kind:
                return Ok(source)

        return Err(
            [
                world_errors.SourceConfigNotConfigured(
                    source_id=kind,
                    kind=kind,
                )
            ]
        )

    def find_source_for_extension(self, extension: str) -> SourceConfigValue | None:
        for source in self._sources_instances:
            if source.supports_extension(extension):
                return source

        return None

    def supported_extensions(self) -> set[str]:
        extensions: set[str] = set()

        for source in self._sources_instances:
            extensions.add(source.extension)

        return extensions


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
