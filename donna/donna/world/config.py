import pathlib
import tomllib
from typing import Any

import pydantic

from donna.core import utils
from donna.core.entities import BaseEntity
from donna.domain.ids import PythonImportPath, WorldId
from donna.machine.primitives import resolve_primitive
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
                "kind": PythonImportPath.parse("donna.lib.sources.markdown"),
            }
        ),
    ]


def _default_worlds() -> list[WorldConfig]:
    _donna = DONNA_DIR_NAME

    project_dir = utils.discover_project_dir(_donna)

    return [
        WorldConfig.model_validate(
            {
                "id": WorldId("donna"),
                "kind": PythonImportPath.parse("donna.lib.worlds.python"),
                "readonly": True,
                "session": False,
                "package": "donna",
            }
        ),
        WorldConfig.model_validate(
            {
                "id": WorldId("home"),
                "kind": PythonImportPath.parse("donna.lib.worlds.filesystem"),
                "readonly": True,
                "session": False,
                "path": pathlib.Path.home() / _donna / DONNA_WORLD_HOME_DIR_NAME,
            }
        ),
        WorldConfig.model_validate(
            {
                "id": WorldId("project"),
                "kind": PythonImportPath.parse("donna.lib.worlds.filesystem"),
                "readonly": False,
                "session": False,
                "path": project_dir / _donna / DONNA_WORLD_PROJECT_DIR_NAME,
            }
        ),
        WorldConfig.model_validate(
            {
                "id": WorldId("session"),
                "kind": PythonImportPath.parse("donna.lib.worlds.filesystem"),
                "readonly": False,
                "session": True,
                "path": project_dir / _donna / DONNA_WORLD_SESSION_DIR_NAME,
            }
        ),
    ]


class Config(BaseEntity):
    worlds: list[WorldConfig] = pydantic.Field(default_factory=_default_worlds)
    sources: list[SourceConfig] = pydantic.Field(default_factory=_default_sources)
    _worlds_instances: list[BaseWorld] = pydantic.PrivateAttr(default_factory=list)
    _sources_instances: list[SourceConfigValue] = pydantic.PrivateAttr(default_factory=list)

    tmp_dir: pathlib.Path = pathlib.Path("./tmp")

    def model_post_init(self, __context: Any) -> None:
        worlds: list[BaseWorld] = []
        sources: list[SourceConfigValue] = []

        for world_config in self.worlds:
            primitive = resolve_primitive(world_config.kind)

            if not isinstance(primitive, WorldConstructor):
                raise NotImplementedError(f"World constructor '{world_config.kind}' is not supported")

            worlds.append(primitive.construct_world(world_config))

        for source_config in self.sources:
            primitive = resolve_primitive(source_config.kind)

            if not isinstance(primitive, SourceConstructor):
                raise NotImplementedError(f"Source constructor '{source_config.kind}' is not supported")

            sources.append(primitive.construct_source(source_config))

        object.__setattr__(self, "_worlds_instances", worlds)
        object.__setattr__(self, "_sources_instances", sources)

    def get_world(self, world_id: WorldId) -> BaseWorld:
        for world in self._worlds_instances:
            if world.id == world_id:
                return world

        raise NotImplementedError(f"World with id '{world_id}' is not configured")

    @property
    def worlds_instances(self) -> list[BaseWorld]:
        return list(self._worlds_instances)

    @property
    def sources_instances(self) -> list[SourceConfigValue]:
        return list(self._sources_instances)

    def get_source_config(self, kind: str) -> SourceConfigValue:
        for source in self._sources_instances:
            if source.kind == kind:
                return source

        raise NotImplementedError(f"Source config '{kind}' is not configured")

    def find_source_for_extension(self, extension: str) -> SourceConfigValue | None:
        for source in self._sources_instances:
            if source.supports_extension(extension):
                return source

        return None

    def supported_extensions(self) -> list[str]:
        extensions: list[str] = []

        for source in self._sources_instances:
            for extension in source.supported_extensions:
                if extension not in extensions:
                    extensions.append(extension)

        return extensions


_CONFIG_DIR: pathlib.Path | None = None
_CONFIG: Config | None = None


def config_dir() -> pathlib.Path:
    global _CONFIG_DIR

    if _CONFIG_DIR:
        return _CONFIG_DIR

    _CONFIG_DIR = utils.discover_project_dir(DONNA_DIR_NAME) / DONNA_DIR_NAME

    return _CONFIG_DIR


def config() -> Config:
    global _CONFIG

    if _CONFIG:
        return _CONFIG

    config_path = config_dir() / DONNA_CONFIG_NAME

    if config_path.exists():
        _CONFIG = Config.model_validate(tomllib.loads(config_path.read_text()))
    else:
        _CONFIG = Config()

    return _CONFIG
