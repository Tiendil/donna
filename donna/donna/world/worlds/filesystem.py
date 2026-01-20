import importlib.util
import pathlib
import shutil
import types

from donna.domain.ids import ArtifactId, FullArtifactId
from donna.machine.artifacts import Artifact
from donna.world.artifact_builder import construct_artifact_from_content
from donna.world.worlds.base import World as BaseWorld


class World(BaseWorld):
    path: pathlib.Path

    def _artifact_path(self, artifact_id: ArtifactId) -> pathlib.Path:
        return self.path / f"{artifact_id.replace('.', '/')}.md"

    def has(self, artifact_id: ArtifactId) -> bool:
        return self._artifact_path(artifact_id).exists()

    def fetch(self, artifact_id: ArtifactId) -> Artifact:
        path = self._artifact_path(artifact_id)

        if not path.exists():
            raise NotImplementedError(f"Artifact `{artifact_id}` does not exist in world `{self.id}`")

        content = path.read_text(encoding="utf-8")
        full_id = FullArtifactId((self.id, artifact_id))
        return construct_artifact_from_content(full_id, content)

    def fetch_source(self, artifact_id: ArtifactId) -> bytes:
        path = self._artifact_path(artifact_id)

        if not path.exists():
            raise NotImplementedError(f"Artifact `{artifact_id}` does not exist in world `{self.id}`")

        return path.read_bytes()

    def update(self, artifact_id: ArtifactId, content: bytes) -> None:
        if self.readonly:
            raise NotImplementedError(f"World `{self.id}` is read-only")

        path = self._artifact_path(artifact_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def read_state(self, name: str) -> bytes | None:
        if not self.session:
            raise NotImplementedError(f"World `{self.id}` does not support state storage")

        path = self.path / name

        if not path.exists():
            return None

        return path.read_bytes()

    def write_state(self, name: str, content: bytes) -> None:
        if self.readonly:
            raise NotImplementedError(f"World `{self.id}` is read-only")

        if not self.session:
            raise NotImplementedError(f"World `{self.id}` does not support state storage")

        path = self.path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def list_artifacts(self, artifact_prefix: ArtifactId) -> list[ArtifactId]:  # noqa: CCR001
        artifacts: list[ArtifactId] = []

        prefix_path = self.path / artifact_prefix.replace(".", "/")
        artifact_path = prefix_path.with_suffix(".md")

        if artifact_path.exists() and artifact_path.is_file():
            return [artifact_prefix]

        if not prefix_path.exists() or not prefix_path.is_dir():
            return []

        for artifact_file in prefix_path.rglob("*.md"):
            if not artifact_file.is_file():
                continue

            rel_path = artifact_file.relative_to(self.path)
            if rel_path.suffix != ".md":
                continue

            artifact_stem = rel_path.with_suffix("")
            artifacts.append(ArtifactId(".".join(artifact_stem.parts)))

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
