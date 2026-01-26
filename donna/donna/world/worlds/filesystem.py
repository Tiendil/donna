import pathlib
import shutil
from typing import TYPE_CHECKING, cast

from donna.domain.ids import ArtifactId, FullArtifactId, FullArtifactIdPattern
from donna.machine.artifacts import Artifact
from donna.world.utils import ArtifactListingNode, list_artifacts_by_pattern
from donna.world.worlds.base import World as BaseWorld
from donna.world.worlds.base import WorldConstructor

if TYPE_CHECKING:
    from donna.world.config import SourceConfigValue, WorldConfig


class World(BaseWorld):
    path: pathlib.Path

    def _artifact_listing_root(self) -> ArtifactListingNode | None:
        if not self.path.exists():
            return None

        return cast(ArtifactListingNode, self.path)

    def _artifact_path(self, artifact_id: ArtifactId, extension: str) -> pathlib.Path:
        return self.path / f"{artifact_id.replace(':', '/')}{extension}"

    def _resolve_artifact_file(self, artifact_id: ArtifactId) -> pathlib.Path | None:
        artifact_path = self.path / artifact_id.replace(":", "/")
        parent = artifact_path.parent

        if not parent.exists():
            return None

        matches = [path for path in parent.glob(f"{artifact_path.name}.*") if path.is_file()]

        if not matches:
            return None

        if len(matches) > 1:
            raise NotImplementedError(f"Artifact `{artifact_id}` has multiple files in world `{self.id}`")

        return matches[0]

    def _get_source_by_filename(self, filename: str) -> "SourceConfigValue":
        from donna.world.config import config

        extension = pathlib.Path(filename).suffix
        source_config = config().find_source_for_extension(extension)
        if source_config is None:
            raise NotImplementedError(f"Unsupported artifact source extension '{extension}'")

        return source_config

    def has(self, artifact_id: ArtifactId) -> bool:
        return self._resolve_artifact_file(artifact_id) is not None

    def fetch(self, artifact_id: ArtifactId) -> Artifact:
        path = self._resolve_artifact_file(artifact_id)
        if path is None:
            raise NotImplementedError(f"Artifact `{artifact_id}` does not exist in world `{self.id}`")

        content_bytes = path.read_bytes()
        full_id = FullArtifactId((self.id, artifact_id))
        source_config = self._get_source_by_filename(path.name)

        return source_config.construct_artifact_from_bytes(full_id, content_bytes)

    def fetch_source(self, artifact_id: ArtifactId) -> bytes:
        path = self._resolve_artifact_file(artifact_id)
        if path is None:
            raise NotImplementedError(f"Artifact `{artifact_id}` does not exist in world `{self.id}`")

        return path.read_bytes()

    def update(self, artifact_id: ArtifactId, content: bytes, extension: str) -> None:
        if self.readonly:
            raise NotImplementedError(f"World `{self.id}` is read-only")

        path = self._artifact_path(artifact_id, extension)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def file_extension_for(self, artifact_id: ArtifactId) -> str | None:
        path = self._resolve_artifact_file(artifact_id)
        if path is None:
            return None

        return path.suffix

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

    def list_artifacts(self, pattern: FullArtifactIdPattern) -> list[ArtifactId]:  # noqa: CCR001
        from donna.world.config import config

        return list_artifacts_by_pattern(
            world_id=self.id,
            root=self._artifact_listing_root(),
            pattern=pattern,
            supported_extensions=config().supported_extensions(),
        )

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
