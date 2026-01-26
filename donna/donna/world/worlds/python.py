import importlib
import importlib.resources
import pathlib
from typing import TYPE_CHECKING, cast

from donna.domain.ids import ArtifactId, FullArtifactId, FullArtifactIdPattern, WorldId
from donna.machine.artifacts import Artifact
from donna.world.utils import ArtifactListingNode, list_artifacts_by_pattern
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

    def _resolve_artifact_file(self, artifact_id: ArtifactId) -> importlib.resources.abc.Traversable | None:
        parts = str(artifact_id).split(":")
        if not parts:
            return None

        resource_root = self._resource_root()
        if resource_root is None:
            return None

        *dirs, file_name = parts
        resource_dir = resource_root

        for part in dirs:
            resource_dir = resource_dir.joinpath(part)

        if not resource_dir.is_dir():
            return None

        matches = [
            entry for entry in resource_dir.iterdir() if entry.is_file() and entry.name.startswith(f"{file_name}.")
        ]

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
        resource_path = self._resolve_artifact_file(artifact_id)
        if resource_path is None:
            raise NotImplementedError(f"Artifact `{artifact_id}` does not exist in world `{self.id}`")

        content_bytes = resource_path.read_bytes()
        full_id = FullArtifactId((self.id, artifact_id))
        source_config = self._get_source_by_filename(resource_path.name)

        return source_config.construct_artifact_from_bytes(full_id, content_bytes)

    def fetch_source(self, artifact_id: ArtifactId) -> bytes:  # noqa: CCR001
        resource_path = self._resolve_artifact_file(artifact_id)
        if resource_path is None:
            raise NotImplementedError(f"Artifact `{artifact_id}` does not exist in world `{self.id}`")

        return resource_path.read_bytes()

    def update(self, artifact_id: ArtifactId, content: bytes, extension: str) -> None:
        if self.readonly:
            raise NotImplementedError(f"World `{self.id}` is read-only")

        raise NotImplementedError(f"World `{self.id}` is read-only")

    def file_extension_for(self, artifact_id: ArtifactId) -> str | None:
        resource_path = self._resolve_artifact_file(artifact_id)
        if resource_path is None:
            return None

        return pathlib.Path(resource_path.name).suffix

    def list_artifacts(self, pattern: FullArtifactIdPattern) -> list[ArtifactId]:  # noqa: CCR001
        from donna.world.config import config

        return list_artifacts_by_pattern(
            world_id=self.id,
            root=self._artifact_listing_root(),
            pattern=pattern,
            supported_extensions=config().supported_extensions(),
        )

    # TODO: How can the state be represented in the Python world?
    def read_state(self, name: str) -> bytes | None:
        raise NotImplementedError(f"World `{self.id}` does not support state storage")

    def write_state(self, name: str, content: bytes) -> None:
        raise NotImplementedError(f"World `{self.id}` does not support state storage")

    def initialize(self, reset: bool = False) -> None:
        pass

    def is_initialized(self) -> bool:
        return True


class PythonWorldConstructor(WorldConstructor):
    def construct_world(self, config: "WorldConfig") -> Python:
        package = getattr(config, "package", None)

        if package is None:
            raise NotImplementedError(f"World config '{config.id}' does not define a python package")

        module = importlib.import_module(str(package))
        artifacts_root = getattr(module, "donna_artifacts_root", None)

        if artifacts_root is None:
            raise NotImplementedError(f"Package '{package}' does not define donna_artifacts_root")

        if not isinstance(artifacts_root, str):
            raise NotImplementedError(f"Package '{package}' defines invalid donna_artifacts_root")

        return Python(
            id=config.id,
            package=str(package),
            artifacts_root=artifacts_root,
            readonly=config.readonly,
            session=config.session,
        )
