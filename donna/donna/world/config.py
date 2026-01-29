import pathlib
from typing import Any

import pydantic

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import PythonImportPath, WorldId
from donna.machine.primitives import resolve_primitive
from donna.world import errors as world_errors
from donna.world.sources.base import SourceConfig as SourceConfigValue
from donna.world.sources.base import SourceConstructor
from donna.world.worlds.base import World as BaseWorld
from donna.world.worlds.base import WorldConstructor

DONNA_DIR_NAME = ".donna"
DONNA_CONFIG_NAME = "config.toml"
DONNA_WORLD_SESSION_DIR_NAME = "session"
DONNA_WORLD_PROJECT_DIR_NAME = "project"
DONNA_WORLD_HOME_DIR_NAME = "home"


class WorldConfig(BaseEntity):
    kind: PythonImportPath
    id: WorldId
    readonly: bool
    session: bool

    model_config = pydantic.ConfigDict(extra="allow")


class SourceConfig(BaseEntity):
    kind: PythonImportPath

    model_config = pydantic.ConfigDict(extra="allow")


def _default_sources() -> list[SourceConfig]:
    return [
        SourceConfig.model_validate(
            {
                "kind": PythonImportPath.parse_or_raise("donna.lib.sources.markdown"),
            }
        ),
    ]


def _create_default_worlds(project_dir: pathlib.Path) -> list[WorldConfig]:
    return [
        WorldConfig.model_validate(
            {
                "id": WorldId("donna"),
                "kind": PythonImportPath.parse_or_raise("donna.lib.worlds.python"),
                "readonly": True,
                "session": False,
                "package": "donna",
            }
        ),
        WorldConfig.model_validate(
            {
                "id": WorldId("home"),
                "kind": PythonImportPath.parse_or_raise("donna.lib.worlds.filesystem"),
                "readonly": True,
                "session": False,
                "path": pathlib.Path.home() / DONNA_DIR_NAME / DONNA_WORLD_HOME_DIR_NAME,
            }
        ),
        WorldConfig.model_validate(
            {
                "id": WorldId("project"),
                "kind": PythonImportPath.parse_or_raise("donna.lib.worlds.filesystem"),
                "readonly": False,
                "session": False,
                "path": project_dir / DONNA_DIR_NAME / DONNA_WORLD_PROJECT_DIR_NAME,
            }
        ),
        WorldConfig.model_validate(
            {
                "id": WorldId("session"),
                "kind": PythonImportPath.parse_or_raise("donna.lib.worlds.filesystem"),
                "readonly": False,
                "session": True,
                "path": project_dir / DONNA_DIR_NAME / DONNA_WORLD_SESSION_DIR_NAME,
            }
        ),
    ]


def _default_worlds() -> list[WorldConfig]:
    return _create_default_worlds(project_dir())


class Config(BaseEntity):
    worlds: list[WorldConfig] = pydantic.Field(default_factory=_default_worlds)
    sources: list[SourceConfig] = pydantic.Field(default_factory=_default_sources)
    _worlds_instances: list[BaseWorld] = pydantic.PrivateAttr(default_factory=list)
    _sources_instances: list[SourceConfigValue] = pydantic.PrivateAttr(default_factory=list)

    tmp_dir: pathlib.Path = pathlib.Path("./tmp")

    def model_post_init(self, __context: Any) -> None:  # noqa: CCR001
        worlds: list[BaseWorld] = []
        sources: list[SourceConfigValue] = []

        for world_config in self.worlds:
            primitive_result = resolve_primitive(world_config.kind)
            if primitive_result.is_err():
                error = primitive_result.unwrap_err()[0]
                raise ValueError(error.message.format(error=error))

            primitive = primitive_result.unwrap()

            if not isinstance(primitive, WorldConstructor):
                # use exception suitable for pydantic
                raise ValueError(f"World constructor '{world_config.kind}' is not supported")

            worlds.append(primitive.construct_world(world_config))

        for source_config in self.sources:
            primitive_result = resolve_primitive(source_config.kind)
            if primitive_result.is_err():
                error = primitive_result.unwrap_err()[0]
                raise ValueError(error.message.format(error=error))

            primitive = primitive_result.unwrap()

            if not isinstance(primitive, SourceConstructor):
                # use exception suitable for pydantic
                raise ValueError(f"Source constructor '{source_config.kind}' is not supported")

            sources.append(primitive.construct_source(source_config))

        object.__setattr__(self, "_worlds_instances", worlds)
        object.__setattr__(self, "_sources_instances", sources)

    def get_world(self, world_id: WorldId) -> Result[BaseWorld, ErrorsList]:
        for world in self._worlds_instances:
            if world.id == world_id:
                return Ok(world)

        return Err([world_errors.WorldNotConfigured(world_id=world_id)])

    @property
    def worlds_instances(self) -> list[BaseWorld]:
        return list(self._worlds_instances)

    @property
    def sources_instances(self) -> list[SourceConfigValue]:
        return list(self._sources_instances)

    def get_source_config(self, kind: str) -> Result[SourceConfigValue, ErrorsList]:
        for source in self._sources_instances:
            if source.kind == kind:
                return Ok(source)

        return Err([world_errors.SourceConfigNotConfigured(kind=kind)])

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

    def __call__(self) -> V:
        return self.get()


project_dir = GlobalConfig[pathlib.Path]()
config_dir = GlobalConfig[pathlib.Path]()
config = GlobalConfig[Config]()
