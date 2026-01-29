import importlib
import importlib.resources
import pathlib
from typing import TYPE_CHECKING, cast

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import ArtifactId, FullArtifactId, FullArtifactIdPattern, WorldId
from donna.machine.artifacts import Artifact
from donna.world import errors as world_errors
from donna.world.artifacts_discovery import ArtifactListingNode, list_artifacts_by_pattern
from donna.world.worlds.base import World as BaseWorld
from donna.world.worlds.base import WorldConstructor

if TYPE_CHECKING:
    from donna.world.config import SourceConfigValue, WorldConfig


class Python(BaseWorld):
    id: WorldId
    readonly: bool = True
    session: bool = False
    package: str
    artifacts_root: str

    def _resource_root(self) -> importlib.resources.abc.Traversable | None:
        package = self.artifacts_root

        try:
            return importlib.resources.files(package)
        except ModuleNotFoundError:
            return None

    def _artifact_listing_root(self) -> ArtifactListingNode | None:
        root = self._resource_root()
        if root is None:
            return None

        return cast(ArtifactListingNode, root)

    def _resolve_artifact_file(
        self, artifact_id: ArtifactId
    ) -> Result[importlib.resources.abc.Traversable | None, ErrorsList]:
        parts = str(artifact_id).split(":")
        if not parts:
            return Ok(None)

        resource_root = self._resource_root()
        if resource_root is None:
            return Ok(None)

        *dirs, file_name = parts
        resource_dir = resource_root

        for part in dirs:
            resource_dir = resource_dir.joinpath(part)

        if not resource_dir.is_dir():
            return Ok(None)

        matches = [
            entry for entry in resource_dir.iterdir() if entry.is_file() and entry.name.startswith(f"{file_name}.")
        ]

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
    def fetch(self, artifact_id: ArtifactId) -> Result[Artifact, ErrorsList]:
        resource_path = self._resolve_artifact_file(artifact_id).unwrap()
        if resource_path is None:
            return Err([world_errors.ArtifactNotFound(artifact_id=artifact_id, world_id=self.id)])

        content_bytes = resource_path.read_bytes()
        full_id = FullArtifactId((self.id, artifact_id))

        extension = pathlib.Path(resource_path.name).suffix
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

        return Ok(source_config.construct_artifact_from_bytes(full_id, content_bytes).unwrap())

    @unwrap_to_error
    def fetch_source(self, artifact_id: ArtifactId) -> Result[bytes, ErrorsList]:  # noqa: CCR001
        resource_path = self._resolve_artifact_file(artifact_id).unwrap()
        if resource_path is None:
            return Err([world_errors.ArtifactNotFound(artifact_id=artifact_id, world_id=self.id)])

        return Ok(resource_path.read_bytes())

    def update(self, artifact_id: ArtifactId, content: bytes, extension: str) -> Result[None, ErrorsList]:
        return Err([world_errors.WorldReadonly(world_id=self.id)])

    @unwrap_to_error
    def file_extension_for(self, artifact_id: ArtifactId) -> Result[str, ErrorsList]:
        resource_path = self._resolve_artifact_file(artifact_id).unwrap()
        if resource_path is None:
            return Err([world_errors.ArtifactNotFound(artifact_id=artifact_id, world_id=self.id)])

        return Ok(pathlib.Path(resource_path.name).suffix)

    def list_artifacts(self, pattern: FullArtifactIdPattern) -> list[ArtifactId]:  # noqa: CCR001
        return list_artifacts_by_pattern(
            world_id=self.id,
            root=self._artifact_listing_root(),
            pattern=pattern,
        )

    # TODO: How can the state be represented in the Python world?
    def read_state(self, name: str) -> Result[bytes | None, ErrorsList]:
        return Err([world_errors.WorldStateStorageUnsupported(world_id=self.id)])

    def write_state(self, name: str, content: bytes) -> Result[None, ErrorsList]:
        return Err([world_errors.WorldStateStorageUnsupported(world_id=self.id)])

    def initialize(self, reset: bool = False) -> None:
        pass

    def is_initialized(self) -> bool:
        return True


class PythonWorldConstructor(WorldConstructor):
    def construct_world(self, config: "WorldConfig") -> Python:
        package = getattr(config, "package", None)

        if package is None:
            raise ValueError(f"World config '{config.id}' does not define a python package")

        module = importlib.import_module(str(package))
        artifacts_root = getattr(module, "donna_artifacts_root", None)

        if artifacts_root is None:
            raise ValueError(f"Package '{package}' does not define donna_artifacts_root")

        if not isinstance(artifacts_root, str):
            raise ValueError(f"Package '{package}' defines invalid donna_artifacts_root")

        return Python(
            id=config.id,
            package=str(package),
            artifacts_root=artifacts_root,
            readonly=config.readonly,
            session=config.session,
        )
