import importlib.util
import pathlib
import tomllib
import types

import pydantic

from donna.core import utils
from donna.core.entities import BaseEntity
from donna.domain.ids import ArtifactId, NamespaceId, WorldId


DONNA_DIR_NAME = ".donna"
DONNA_CONFIG_NAME = "donna.toml"
DONNA_DESSION_DIR_NAME = "session"


class World(BaseEntity):
    id: WorldId
    readonly: bool = True
    session: bool = False

    def has(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> bool:
        raise NotImplementedError("You must implement this method in subclasses")

    def read(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> bytes:
        raise NotImplementedError("You must implement this method in subclasses")

    def write(self, namespace_id: NamespaceId, artifact_id: ArtifactId, content: bytes) -> None:
        raise NotImplementedError("You must implement this method in subclasses")

    def list_artifacts(self, namespace_id: NamespaceId) -> list[ArtifactId]:
        raise NotImplementedError("You must implement this method in subclasses")

    def get_modules(self) -> list[types.ModuleType]:
        raise NotImplementedError("You must implement this method in subclasses")


class WorldFilesystem(World):
    path: pathlib.Path

    def _artifact_path(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> pathlib.Path:
        return self.path / namespace_id / f"{artifact_id.replace('.', '/')}.md"

    def has(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> bool:
        return self._artifact_path(namespace_id, artifact_id).exists()

    def read(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> bytes:
        path = self._artifact_path(namespace_id, artifact_id)

        if not path.exists():
            raise NotImplementedError(f"Artifact `{id}` does not exist in world `{self.id}`")

        return path.read_bytes()

    def write(self, namespace_id: NamespaceId, artifact_id: ArtifactId, content: bytes) -> None:
        if self.readonly:
            raise NotImplementedError(f"World `{self.id}` is read-only")

        path = self._artifact_path(namespace_id, artifact_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def list_artifacts(self, namespace_id: NamespaceId) -> list[ArtifactId]:
        path = self.path / namespace_id

        if not path.exists() or not path.is_dir():
            return []

        artifacts: list[ArtifactId] = []

        for artifact_file in path.iterdir():
            if not artifact_file.is_file():
                continue

            if not artifact_file.suffix == ".md":
                continue

            artifacts.append(ArtifactId(artifact_file.stem))

        return artifacts

    def get_modules(self) -> list[types.ModuleType]:
        # load only top-level .py files
        # it is the responsibility of the developer to import submodules within those files
        # if required

        modules = []

        code_path = self.path / "code"

        for module_file in code_path.glob("*.py"):
            relative_path = module_file.relative_to(self.path)
            module_name = f"donna._world_code.{self.id}.{relative_path.stem}"
            module_spec = importlib.util.spec_from_file_location(module_name, module_file)

            if module_spec is None or module_spec.loader is None:
                raise NotImplementedError(f"Cannot load workflow module from '{module_file}'")

            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)

            modules.append(module)

        return modules


# TODO: refactor donna to use importlib.resources and enable WorldPackage


def _default_worlds() -> list["WorldFilesystem"]:
    _donna = DONNA_DIR_NAME

    return [
        WorldFilesystem(
            id=WorldId("donna"),
            path=pathlib.Path(__file__).parent.parent / "std",
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
            path=utils.project_dir(_donna) / _donna,
            readonly=False,
            session=False,
        ),
        WorldFilesystem(
            id=WorldId("session"),
            path=utils.project_dir(_donna) / _donna / DONNA_DESSION_DIR_NAME,
            readonly=False,
            session=True,
        ),
    ]


class Config(BaseEntity):
    worlds: list[WorldFilesystem] = pydantic.Field(default_factory=_default_worlds)

    def get_world(self, world_id: WorldId) -> World:
        for world in self.worlds:
            if world.id == world_id:
                return world

        raise NotImplementedError(f"World with id '{world_id}' is not configured")


_CONFIG: Config | None = None


def config() -> Config:
    global _CONFIG

    if _CONFIG:
        return _CONFIG

    config_path = utils.project_dir(DONNA_DIR_NAME) / DONNA_CONFIG_NAME

    if config_path.exists():
        _CONFIG = Config.model_validate(tomllib.loads(config_path.read_text()))
    else:
        _CONFIG = Config()

    return _CONFIG
