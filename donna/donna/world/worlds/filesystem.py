import pathlib
import shutil
from typing import TYPE_CHECKING, cast

from donna.domain.ids import ArtifactId, FullArtifactId
from donna.machine.artifacts import Artifact
from donna.world.sources import markdown as markdown_source
from donna.world.worlds.base import World as BaseWorld
from donna.world.worlds.base import WorldConstructor

if TYPE_CHECKING:
    from donna.world.config import WorldConfig


class World(BaseWorld):
    path: pathlib.Path

    def _artifact_markdown_path(self, artifact_id: ArtifactId) -> pathlib.Path:
        return self.path / f"{artifact_id.replace(':', '/')}.md"

    def has(self, artifact_id: ArtifactId) -> bool:
        return self._artifact_markdown_path(artifact_id).exists()

    def fetch(self, artifact_id: ArtifactId) -> Artifact:
        markdown_path = self._artifact_markdown_path(artifact_id)

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

        raise NotImplementedError(f"Artifact `{artifact_id}` does not exist in world `{self.id}`")

    def fetch_source(self, artifact_id: ArtifactId) -> bytes:
        markdown_path = self._artifact_markdown_path(artifact_id)

        if markdown_path.exists():
            return markdown_path.read_bytes()

        raise NotImplementedError(f"Artifact `{artifact_id}` does not exist in world `{self.id}`")

    def update(self, artifact_id: ArtifactId, content: bytes) -> None:
        if self.readonly:
            raise NotImplementedError(f"World `{self.id}` is read-only")

        path = self._artifact_markdown_path(artifact_id)

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

        if markdown_path.exists() and markdown_path.is_file():
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

        return sorted(artifacts, key=str)

    def initialize(self, reset: bool = False) -> None:
        if self.readonly:
            return

        if self.path.exists() and reset:
            shutil.rmtree(self.path)

        self.path.mkdir(parents=True, exist_ok=True)

    def is_initialized(self) -> bool:
        return self.path.exists()


class FilesystemWorldConstructor(WorldConstructor):
    def construct_world(self, config: "WorldConfig") -> World:
        path_value = getattr(config, "path", None)

        if path_value is None:
            raise NotImplementedError(f"World config '{config.id}' does not define a filesystem path")

        return World(
            id=config.id,
            path=pathlib.Path(path_value),
            readonly=config.readonly,
            session=config.session,
        )
