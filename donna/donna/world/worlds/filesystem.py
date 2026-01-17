import importlib.util
import pathlib
import shutil
import types

from donna.domain.ids import ArtifactId, FullArtifactId, NamespaceId
from donna.machine.artifacts import Artifact
from donna.world.artifact_builder import construct_artifact_from_content
from donna.world.worlds.base import World as BaseWorld


class World(BaseWorld):
    path: pathlib.Path

    def _artifact_path(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> pathlib.Path:
        return self.path / namespace_id / f"{artifact_id.replace('.', '/')}.md"

    def has(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> bool:
        return self._artifact_path(namespace_id, artifact_id).exists()

    def fetch(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> Artifact:
        path = self._artifact_path(namespace_id, artifact_id)

        if not path.exists():
            raise NotImplementedError(f"Artifact `{id}` does not exist in world `{self.id}`")

        content = path.read_text(encoding="utf-8")
        full_id = FullArtifactId((self.id, namespace_id, artifact_id))
        return construct_artifact_from_content(full_id, content)

    def fetch_source(self, namespace_id: NamespaceId, artifact_id: ArtifactId) -> bytes:
        path = self._artifact_path(namespace_id, artifact_id)

        if not path.exists():
            raise NotImplementedError(f"Artifact `{id}` does not exist in world `{self.id}`")

        return path.read_bytes()

    def update(self, namespace_id: NamespaceId, artifact_id: ArtifactId, content: bytes) -> None:
        if self.readonly:
            raise NotImplementedError(f"World `{self.id}` is read-only")

        path = self._artifact_path(namespace_id, artifact_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def read_state(self, name: str) -> bytes:
        if not self.session:
            raise NotImplementedError(f"World `{self.id}` does not support state storage")

        path = self.path / name

        if not path.exists():
            raise NotImplementedError(f"State `{name}` does not exist in world `{self.id}`")

        return path.read_bytes()

    def write_state(self, name: str, content: bytes) -> None:
        if self.readonly:
            raise NotImplementedError(f"World `{self.id}` is read-only")

        if not self.session:
            raise NotImplementedError(f"World `{self.id}` does not support state storage")

        path = self.path / name
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

    def initialize(self, reset: bool = False) -> None:
        if self.readonly:
            return

        if self.path.exists() and reset:
            shutil.rmtree(self.path)

        self.path.mkdir(parents=True, exist_ok=True)

    def is_initialized(self) -> bool:
        return self.path.exists()
