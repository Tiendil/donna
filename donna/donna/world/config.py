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

    def has(self, id: str) -> bool:
        raise NotImplementedError("You must implement this method in subclasses")

    def extract(self, id: str) -> str:
        raise NotImplementedError("You must implement this method in subclasses")


class WorldFilesystem(World):
    path: pathlib.Path

    def has(self, id: str) -> bool:
        artifact_path = self.path / id
        print(artifact_path)
        return artifact_path.exists()

    def extract(self, id: str) -> str:
        artifact_path = self.path / id

        if not artifact_path.exists():
            raise NotImplementedError(f"Artifact `{id}` does not exist in world `{self.id}`")

        return artifact_path.read_text()


# TODO: refactor donna to use importlib.resources and enable this class
# class WorldPackage(World):
#     name: str


def _default_worlds():
    _donna = DONNA_DIR_NAME

    return [
        WorldFilesystem(
            id=WorldId("donna"),
            path=pathlib.Path(__file__).parent.parent / "std",
            readonly=True,
            store_session=False,
        ),
        WorldFilesystem(
            id=WorldId("home"),
            path=pathlib.Path.home() / _donna,
            readonly=True,
            store_session=False,
        ),
        WorldFilesystem(
            id=WorldId("project"),
            path=utils.project_dir(_donna) / _donna,
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
