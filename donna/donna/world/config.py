import pathlib
import importlib
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

    def get_module_sources(self) -> list[str]:
        raise NotImplementedError("You must implement this method in subclasses")


class WorldFilesystem(World):
    path: pathlib.Path

    def has(self, id: str) -> bool:
        artifact_path = self.path / id
        return artifact_path.exists()

    def extract(self, id: str) -> str:
        artifact_path = self.path / id

        if not artifact_path.exists():
            raise NotImplementedError(f"Artifact `{id}` does not exist in world `{self.id}`")

        return artifact_path.read_text()

    def get_modules(self) -> list[importlib.machinery.ModuleSpec]:
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
