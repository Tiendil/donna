import importlib
import importlib.resources
import pathlib
from typing import TYPE_CHECKING

from donna.domain.ids import ArtifactId, FullArtifactId, FullArtifactIdPattern, WorldId
from donna.machine.artifacts import Artifact
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

    def _extension_priorities(self) -> dict[str, int]:
        from donna.world.config import config

        priorities: dict[str, int] = {}
        priority = 0

        for source in config().sources_instances:
            for extension in source.supported_extensions:
                if extension not in priorities:
                    priorities[extension] = priority
                    priority += 1

        return priorities

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

    def _list_artifacts_by_extension(self) -> list[ArtifactId]:  # noqa: CCR001
        resource_artifacts: dict[ArtifactId, int] = {}
        priorities = self._extension_priorities()

        def walk(  # noqa: CCR001
            node: importlib.resources.abc.Traversable,
            parts: list[str],
            base_parts: list[str],
        ) -> None:
            for entry in node.iterdir():
                if entry.is_dir():
                    walk(entry, parts + [entry.name], base_parts)
                    continue

                if not entry.is_file():
                    continue

                extension = pathlib.Path(entry.name).suffix.lower()
                if extension not in priorities:
                    continue

                stem = entry.name[: -len(extension)]
                artifact_name = ":".join(base_parts + parts + [stem])
                if ArtifactId.validate(artifact_name):
                    artifact_id = ArtifactId(artifact_name)
                    priority = priorities[extension]
                    if artifact_id not in resource_artifacts or priority < resource_artifacts[artifact_id]:
                        resource_artifacts[artifact_id] = priority

        resource_root = self._resource_root()
        if resource_root is None:
            return list(resource_artifacts.keys())

        base_path = resource_root
        base_parts: list[str] = []

        if base_path.is_dir():
            walk(base_path, [], base_parts)

        return list(resource_artifacts.keys())

    def list_artifacts(self, pattern: FullArtifactIdPattern) -> list[ArtifactId]:  # noqa: CCR001
        if pattern[0] not in {"*", "**"} and pattern[0] != str(self.id):
            return []

        artifacts = self._list_artifacts_by_extension()
        matched: list[ArtifactId] = []

        for artifact_id in artifacts:
            full_id = FullArtifactId((self.id, artifact_id))
            if pattern.matches_full_id(full_id):
                matched.append(artifact_id)

        return matched

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
