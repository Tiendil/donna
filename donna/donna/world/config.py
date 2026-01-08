import pathlib

import pydantic

from donna.core import utils
from donna.domain.types import WorldId
from donna.core.entities import BaseEntity


DONNA_DIR_NAME = ".donna"
DONNA_CONFIG_NAME = "donna.toml"


class World(BaseEntity):
    id: WorldId
    readonly: bool = True
    store_session: bool = False


class WorldFilesystem(World):
    path: pathlib.Path


# TODO: refactor donna to use importlib.resources and enable this class
# class WorldPackage(World):
#     name: str


def _default_worlds():
    _donna = DONNA_DIR_NAME

    return [
        WorldFilesystem(
            id=WorldId("donna"),
            root=pathlib.Path(__file__).parent.parent / _donna,
            readonly=True,
            store_session=False,
        ),
        WorldFilesystem(
            id=WorldId("home"),
            root=pathlib.Path.home() / _donna,
            readonly=True,
            store_session=False,
        ),
        WorldFilesystem(
            id=WorldId("project"),
            root=utils.project_dir(_donna) / _donna,
            readonly=False,
            store_session=True,
        ),
    ]


class Config(BaseEntity):
    worlds: list[WorldFilesystem] = pydantic.Field(default_factory=_default_worlds)


_CONFIG: Config | None = None


def config() -> Config:
    global _CONFIG

    if _CONFIG:
        return _CONFIG

    config_path = utils.project_dir(DONNA_DIR_NAME) / DONNA_CONFIG_NAME

    if config_path.exists():
        _CONFIG = Config.from_toml(config_path.read_text())
    else:
        _CONFIG = Config()

    return _CONFIG
