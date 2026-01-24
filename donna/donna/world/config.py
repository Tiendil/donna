import pathlib
import tomllib
from typing import TypeVar

import pydantic

from donna.core import utils
from donna.core.entities import BaseEntity
from donna.domain.ids import WorldId
from donna.world.sources import markdown as markdown_source
from donna.world.sources import python as python_source
from donna.world.sources.base import SourceConfig
from donna.world.worlds.base import World as BaseWorld
from donna.world.worlds.filesystem import World as WorldFilesystem
from donna.world.worlds.python import Python as WorldPython

DONNA_DIR_NAME = ".donna"
DONNA_CONFIG_NAME = "donna.toml"
DONNA_DESSION_DIR_NAME = "session"

# TODO: refactor donna to use importlib.resources and enable WorldPackage


WorldConfig = WorldFilesystem | WorldPython
SourceConfigValue = SourceConfig
SOURCE_CONFIG = TypeVar("SOURCE_CONFIG", bound=SourceConfig)


def _default_sources() -> list[SourceConfigValue]:
    return [
        markdown_source.Config(),
        python_source.Config(),
    ]


def _default_worlds() -> list[WorldConfig]:
    _donna = DONNA_DIR_NAME

    project_dir = utils.discover_project_dir(_donna)

    return [
        WorldPython(
            id=WorldId("donna"),
            root="donna.std",
            readonly=True,
            session=False,
        ),
        WorldFilesystem(
            id=WorldId("home"),
            path=pathlib.Path.home() / _donna,
            readonly=True,
            session=False,
        ),
        WorldFilesystem(
            id=WorldId("project"),
            path=project_dir / _donna,
            readonly=False,
            session=False,
        ),
        WorldFilesystem(
            id=WorldId("session"),
            path=project_dir / _donna / DONNA_DESSION_DIR_NAME,
            readonly=False,
            session=True,
        ),
    ]


class Config(BaseEntity):
    worlds: list[WorldConfig] = pydantic.Field(default_factory=_default_worlds)
    sources: list[SourceConfigValue] = pydantic.Field(default_factory=_default_sources)

    def get_world(self, world_id: WorldId) -> BaseWorld:
        for world in self.worlds:
            if world.id == world_id:
                return world

        raise NotImplementedError(f"World with id '{world_id}' is not configured")

    def get_source_config(self, source_config_type: type[SOURCE_CONFIG]) -> SOURCE_CONFIG:
        for source in self.sources:
            if isinstance(source, source_config_type):
                return source

        raise NotImplementedError(f"Source config '{source_config_type.__name__}' is not configured")


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
