import pathlib
import shutil
from functools import lru_cache
from typing import TYPE_CHECKING

from donna.domain.ids import ArtifactId, FullArtifactId, FullArtifactIdPattern
from donna.machine.artifacts import Artifact
from donna.world.worlds.base import World as BaseWorld
from donna.world.worlds.base import WorldConstructor

if TYPE_CHECKING:
    from donna.world.config import SourceConfigValue, WorldConfig


def _pattern_allows_prefix(pattern_parts: tuple[str, ...], prefix_parts: tuple[str, ...]) -> bool:
    @lru_cache(maxsize=None)
    def match_at(p_index: int, v_index: int) -> bool:  # noqa: CCR001
        if v_index >= len(prefix_parts):
            return True

        if p_index >= len(pattern_parts):
            return False

        token = pattern_parts[p_index]

        if token == "**":  # noqa: S105
            return match_at(p_index + 1, v_index) or match_at(p_index, v_index + 1)

        if token == "*" or token == prefix_parts[v_index]:  # noqa: S105
            return match_at(p_index + 1, v_index + 1)

        return False

    return match_at(0, 0)


class World(BaseWorld):
    path: pathlib.Path

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

    def _list_artifacts(self, pattern: FullArtifactIdPattern) -> list[ArtifactId]:  # noqa: CCR001
        from donna.world.config import config

        if pattern[0] not in {"*", "**"} and pattern[0] != str(self.id):
            return []

        if not self.path.exists():
            return []

        supported_extensions = config().supported_extensions()
        artifacts: set[ArtifactId] = set()
        pattern_parts = tuple(pattern)
        world_prefix = (str(self.id),)

        def walk(node: pathlib.Path, parts: list[str]) -> None:  # noqa: CCR001
            for entry in sorted(node.iterdir()):
                if entry.is_dir():
                    next_parts = parts + [entry.name]
                    if not _pattern_allows_prefix(pattern_parts, world_prefix + tuple(next_parts)):
                        continue
                    walk(entry, next_parts)
                    continue

                if not entry.is_file():
                    continue

                extension = entry.suffix.lower()
                if extension not in supported_extensions:
                    continue

                stem = entry.stem
                artifact_name = ":".join(parts + [stem])
                if ArtifactId.validate(artifact_name):
                    artifact_id = ArtifactId(artifact_name)
                    full_id = FullArtifactId((self.id, artifact_id))
                    if pattern.matches_full_id(full_id):
                        artifacts.add(artifact_id)

        walk(self.path, [])

        return list(sorted(artifacts))

    def list_artifacts(self, pattern: FullArtifactIdPattern) -> list[ArtifactId]:  # noqa: CCR001
        return self._list_artifacts(pattern)

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
