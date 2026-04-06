from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING, Any

import pydantic

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.python_path import PythonPath
from donna.machine.primitives import resolve_primitive
from donna.workspaces import errors as world_errors
from donna.workspaces.sources.base import SourceConfig as SourceConfigValue
from donna.workspaces.sources.base import SourceConstructor
from donna.workspaces.worlds.base import World as BaseWorld

if TYPE_CHECKING:
    from donna.protocol.modes import Mode

DONNA_DIR_NAME = ".donna"
DONNA_CONFIG_NAME = "config.toml"
DONNA_WORLD_SESSION_DIR_NAME = "session"
DONNA_WORLD_PROJECT_DIR_NAME = "project"


class SourceConfig(BaseEntity):
    kind: PythonPath

    model_config = pydantic.ConfigDict(extra="allow")


def _default_sources() -> list[SourceConfig]:
    return [
        SourceConfig.model_validate(
            {
                "kind": "donna.lib.sources.markdown",
            }
        ),
    ]


def _construct_project_world() -> BaseWorld:
    from donna.workspaces.worlds.filesystem import World as FilesystemWorld

    return FilesystemWorld(
        id=DONNA_WORLD_PROJECT_DIR_NAME,
        path=project_dir().resolve(),
    )


class Config(BaseEntity):
    sources: list[SourceConfig] = pydantic.Field(default_factory=_default_sources)
    _project_world: BaseWorld | None = pydantic.PrivateAttr(default=None)
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

        object.__setattr__(self, "_project_world", _construct_project_world())
        object.__setattr__(self, "_sources_instances", sources)

    @property
    def project_world(self) -> BaseWorld:
        if self._project_world is None:
            raise world_errors.GlobalConfigNotSet()

        return self._project_world

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
            for extension in source.supported_extensions:
                extensions.add(extension)

        return extensions


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
config_dir = GlobalConfig[pathlib.Path]()
config = GlobalConfig[Config]()
protocol: GlobalConfig["Mode"] = GlobalConfig()
