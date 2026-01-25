import importlib.util
import pathlib
import shutil
from types import ModuleType
from typing import cast

from donna.domain.ids import ArtifactId, FullArtifactId
from donna.machine.artifacts import Artifact
from donna.world.sources import markdown as markdown_source
from donna.world.sources import python as python_source
from donna.world.worlds.base import World as BaseWorld


class World(BaseWorld):
    path: pathlib.Path

    def _artifact_markdown_path(self, artifact_id: ArtifactId) -> pathlib.Path:
        return self.path / f"{artifact_id.replace(':', '/')}.md"

    def _artifact_python_path(self, artifact_id: ArtifactId) -> pathlib.Path:
        return self.path / f"{artifact_id.replace(':', '/')}.py"

    def has(self, artifact_id: ArtifactId) -> bool:
        return self._artifact_markdown_path(artifact_id).exists() or self._artifact_python_path(artifact_id).exists()

    def fetch(self, artifact_id: ArtifactId) -> Artifact:
        markdown_path = self._artifact_markdown_path(artifact_id)
        python_path = self._artifact_python_path(artifact_id)

        if markdown_path.exists():
            content = markdown_path.read_text(encoding="utf-8")
            full_id = FullArtifactId((self.id, artifact_id))
            from donna.world.config import config

            source_config = cast(markdown_source.Config, config().get_source_config("markdown"))
            return markdown_source.construct_artifact_from_markdown_source(
                full_id,
                content,
                source_config,
            )

        if python_path.exists():
            module = self._load_module_from_path(artifact_id, python_path)
            full_id = FullArtifactId((self.id, artifact_id))
            return python_source.construct_artifact_from_module(module, full_id)

        raise NotImplementedError(f"Artifact `{artifact_id}` does not exist in world `{self.id}`")

    def fetch_source(self, artifact_id: ArtifactId) -> bytes:
        markdown_path = self._artifact_markdown_path(artifact_id)
        python_path = self._artifact_python_path(artifact_id)

        if markdown_path.exists():
            return markdown_path.read_bytes()

        if python_path.exists():
            return python_path.read_bytes()

        raise NotImplementedError(f"Artifact `{artifact_id}` does not exist in world `{self.id}`")

    def update(self, artifact_id: ArtifactId, content: bytes) -> None:
        if self.readonly:
            raise NotImplementedError(f"World `{self.id}` is read-only")

        markdown_path = self._artifact_markdown_path(artifact_id)
        python_path = self._artifact_python_path(artifact_id)

        if python_path.exists() and not markdown_path.exists():
            path = python_path
        else:
            path = markdown_path

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
        artifacts: set[ArtifactId] = set()

        prefix_path = self.path / artifact_prefix.replace(":", "/")
        markdown_path = prefix_path.with_suffix(".md")
        python_path = prefix_path.with_suffix(".py")

        if markdown_path.exists() and markdown_path.is_file():
            return [artifact_prefix]

        if python_path.exists() and python_path.is_file():
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
            artifacts.add(ArtifactId(":".join(artifact_stem.parts)))

        for artifact_file in prefix_path.rglob("*.py"):
            if not artifact_file.is_file():
                continue

            rel_path = artifact_file.relative_to(self.path)
            if rel_path.suffix != ".py":
                continue

            artifact_stem = rel_path.with_suffix("")
            artifacts.add(ArtifactId(":".join(artifact_stem.parts)))

        return sorted(artifacts, key=str)

    def _load_module_from_path(self, artifact_id: ArtifactId, path: pathlib.Path) -> ModuleType:
        module_name = f"donna.world.filesystem.{self.id}.{artifact_id.replace(':', '.')}"
        spec = importlib.util.spec_from_file_location(module_name, path)

        if spec is None or spec.loader is None:
            raise NotImplementedError(f"Module `{artifact_id}` cannot be imported from `{path}`")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def initialize(self, reset: bool = False) -> None:
        if self.readonly:
            return

        if self.path.exists() and reset:
            shutil.rmtree(self.path)

        self.path.mkdir(parents=True, exist_ok=True)

    def is_initialized(self) -> bool:
        return self.path.exists()
