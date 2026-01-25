import pathlib
import tomllib
from typing import Any

import pydantic

from donna.core import utils
from donna.core.entities import BaseEntity
from donna.domain.ids import PythonImportPath, WorldId
from donna.machine.primitives import resolve_primitive
from donna.world.sources import markdown as markdown_source
from donna.world.sources.base import SourceConfig
from donna.world.worlds.base import World as BaseWorld
from donna.world.worlds.base import WorldConstructor

DONNA_DIR_NAME = ".donna"
DONNA_CONFIG_NAME = "donna.toml"
DONNA_DESSION_DIR_NAME = "session"

# TODO: refactor donna to use importlib.resources and enable WorldPackage


class WorldConfig(BaseEntity):
    kind: PythonImportPath
    id: WorldId
    readonly: bool
    session: bool

    model_config = pydantic.ConfigDict(extra="allow")


SourceConfigValue = SourceConfig


def _default_sources() -> list[SourceConfigValue]:
    return [
        markdown_source.Config(),
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
                "root": "donna.std",
            }
        ),
        WorldConfig.model_validate(
            {
                "id": WorldId("home"),
                "kind": PythonImportPath.parse("donna.lib.worlds.filesystem"),
                "readonly": True,
                "session": False,
                "path": pathlib.Path.home() / _donna,
            }
        ),
        WorldConfig.model_validate(
            {
                "id": WorldId("project"),
                "kind": PythonImportPath.parse("donna.lib.worlds.filesystem"),
                "readonly": False,
                "session": False,
                "path": project_dir / _donna,
            }
        ),
        WorldConfig.model_validate(
            {
                "id": WorldId("session"),
                "kind": PythonImportPath.parse("donna.lib.worlds.filesystem"),
                "readonly": False,
                "session": True,
                "path": project_dir / _donna / DONNA_DESSION_DIR_NAME,
            }
        ),
    ]


class Config(BaseEntity):
    worlds: list[WorldConfig] = pydantic.Field(default_factory=_default_worlds)
    sources: list[SourceConfigValue] = pydantic.Field(default_factory=_default_sources)
    _worlds_instances: list[BaseWorld] = pydantic.PrivateAttr(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        worlds: list[BaseWorld] = []

        for world_config in self.worlds:
            primitive = resolve_primitive(world_config.kind)

            if not isinstance(primitive, WorldConstructor):
                raise NotImplementedError(f"World constructor '{world_config.kind}' is not supported")

            worlds.append(primitive.construct_world(world_config))

        object.__setattr__(self, "_worlds_instances", worlds)

    def get_world(self, world_id: WorldId) -> BaseWorld:
        for world in self._worlds_instances:
            if world.id == world_id:
                return world

        raise NotImplementedError(f"World with id '{world_id}' is not configured")

    @property
    def worlds_instances(self) -> list[BaseWorld]:
        return list(self._worlds_instances)

    def get_source_config(self, kind: str) -> SourceConfigValue:
        for source in self.sources:
            if source.kind == kind:
                return source

        raise NotImplementedError(f"Source config '{kind}' is not configured")


_CONFIG: Config | None = None


def config() -> Config:
    global _CONFIG

    if _CONFIG:
        return _CONFIG

    config_path = utils.discover_project_dir(DONNA_DIR_NAME) / DONNA_CONFIG_NAME

    if config_path.exists():
        _CONFIG = Config.model_validate(tomllib.loads(config_path.read_text()))
    else:
        _CONFIG = Config()

    return _CONFIG
