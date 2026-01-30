import pathlib
import shutil
from typing import TYPE_CHECKING, cast

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import ArtifactId, FullArtifactId, FullArtifactIdPattern
from donna.machine.artifacts import Artifact
from donna.world import errors as world_errors
from donna.world.artifacts import ArtifactRenderContext
from donna.world.artifacts_discovery import ArtifactListingNode, list_artifacts_by_pattern
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

    def _resolve_artifact_file(self, artifact_id: ArtifactId) -> Result[pathlib.Path | None, ErrorsList]:
        artifact_path = self.path / artifact_id.replace(":", "/")
        parent = artifact_path.parent

        if not parent.exists():
            return Ok(None)

        matches = [path for path in parent.glob(f"{artifact_path.name}.*") if path.is_file()]

        if not matches:
            return Ok(None)

        if len(matches) > 1:
            return Err([world_errors.ArtifactMultipleFiles(artifact_id=artifact_id, world_id=self.id)])

        return Ok(matches[0])

    def _get_source_by_filename(
        self, artifact_id: ArtifactId, filename: str
    ) -> Result["SourceConfigValue", ErrorsList]:
        from donna.world.config import config

        extension = pathlib.Path(filename).suffix
        source_config = config().find_source_for_extension(extension)
        if source_config is None:
            return Err(
                [
                    world_errors.UnsupportedArtifactSourceExtension(
                        artifact_id=artifact_id,
                        world_id=self.id,
                        extension=extension,
                    )
                ]
            )

        return Ok(source_config)

    def has(self, artifact_id: ArtifactId) -> bool:
        resolve_result = self._resolve_artifact_file(artifact_id)
        if resolve_result.is_err():
            return True

        return resolve_result.unwrap() is not None

    @unwrap_to_error
    def fetch(self, artifact_id: ArtifactId, render_context: ArtifactRenderContext) -> Result[Artifact, ErrorsList]:
        path = self._resolve_artifact_file(artifact_id).unwrap()
        if path is None:
            return Err([world_errors.ArtifactNotFound(artifact_id=artifact_id, world_id=self.id)])

        content_bytes = path.read_bytes()
        full_id = FullArtifactId((self.id, artifact_id))

        extension = pathlib.Path(path.name).suffix
        from donna.world.config import config

        source_config = config().find_source_for_extension(extension)
        if source_config is None:
            return Err(
                [
                    world_errors.UnsupportedArtifactSourceExtension(
                        artifact_id=artifact_id,
                        world_id=self.id,
                        extension=extension,
                    )
                ]
            )

        return Ok(source_config.construct_artifact_from_bytes(full_id, content_bytes, render_context).unwrap())

    @unwrap_to_error
    def fetch_source(self, artifact_id: ArtifactId) -> Result[bytes, ErrorsList]:
        path = self._resolve_artifact_file(artifact_id).unwrap()
        if path is None:
            return Err([world_errors.ArtifactNotFound(artifact_id=artifact_id, world_id=self.id)])

        return Ok(path.read_bytes())

    def update(self, artifact_id: ArtifactId, content: bytes, extension: str) -> Result[None, ErrorsList]:
        if self.readonly:
            return Err([world_errors.WorldReadonly(world_id=self.id)])

        path = self._artifact_path(artifact_id, extension)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return Ok(None)

    @unwrap_to_error
    def file_extension_for(self, artifact_id: ArtifactId) -> Result[str, ErrorsList]:
        path = self._resolve_artifact_file(artifact_id).unwrap()
        if path is None:
            return Err([world_errors.ArtifactNotFound(artifact_id=artifact_id, world_id=self.id)])

        return Ok(path.suffix)

    def read_state(self, name: str) -> Result[bytes | None, ErrorsList]:
        if not self.session:
            return Err([world_errors.WorldStateStorageUnsupported(world_id=self.id)])

        path = self.path / name

        if not path.exists():
            return Ok(None)

        return Ok(path.read_bytes())

    def write_state(self, name: str, content: bytes) -> Result[None, ErrorsList]:
        if self.readonly:
            return Err([world_errors.WorldReadonly(world_id=self.id)])

        if not self.session:
            return Err([world_errors.WorldStateStorageUnsupported(world_id=self.id)])

        path = self.path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return Ok(None)

    def list_artifacts(self, pattern: FullArtifactIdPattern) -> list[ArtifactId]:  # noqa: CCR001
        return list_artifacts_by_pattern(
            world_id=self.id,
            root=self._artifact_listing_root(),
            pattern=pattern,
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
            raise ValueError(f"World config '{config.id}' does not define a filesystem path")

        return World(
            id=config.id,
            path=pathlib.Path(path_value),
            readonly=config.readonly,
            session=config.session,
        )
