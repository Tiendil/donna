import os
import pathlib
import shutil
import stat
import time
from collections.abc import Iterable
from typing import TYPE_CHECKING, cast

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import ArtifactId, FullArtifactId, FullArtifactIdPattern
from donna.machine.artifacts import Artifact
from donna.workspaces import errors as world_errors
from donna.workspaces.artifacts import ArtifactRenderContext
from donna.workspaces.artifacts_discovery import ArtifactListingNode, list_artifacts_by_pattern
from donna.workspaces.worlds.base import World as BaseWorld
from donna.workspaces.worlds.base import WorldConstructor

if TYPE_CHECKING:
    from donna.workspaces.config import SourceConfigValue, WorldConfig


class World(BaseWorld):
    path: pathlib.Path
    _journal_file_name = "journal.jsonl"

    def _journal_path(self) -> pathlib.Path:
        return self.path / self._journal_file_name

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

        from donna.workspaces.config import config

        supported_extensions = config().supported_extensions()
        matches = [
            path
            for path in parent.glob(f"{artifact_path.name}.*")
            if path.is_file() and path.suffix.lower() in supported_extensions
        ]

        if not matches:
            return Ok(None)

        if len(matches) > 1:
            return Err([world_errors.ArtifactMultipleFiles(artifact_id=artifact_id, world_id=self.id)])

        return Ok(matches[0])

    def _get_source_by_filename(
        self, artifact_id: ArtifactId, filename: str
    ) -> Result["SourceConfigValue", ErrorsList]:
        from donna.workspaces.config import config

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
        from donna.workspaces.config import config

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
    def remove(self, artifact_id: ArtifactId) -> Result[None, ErrorsList]:
        if self.readonly:
            return Err([world_errors.WorldReadonly(world_id=self.id)])

        path = self._resolve_artifact_file(artifact_id).unwrap()

        if path is None:
            return Ok(None)

        path.unlink()

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

    def journal_reset(self) -> Result[None, ErrorsList]:
        if self.readonly:
            return Err([world_errors.WorldReadonly(world_id=self.id)])

        if not self.session:
            return Err([world_errors.WorldStateStorageUnsupported(world_id=self.id)])

        path = self._journal_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")
        return Ok(None)

    def journal_add(self, content: bytes) -> Result[None, ErrorsList]:
        if self.readonly:
            return Err([world_errors.WorldReadonly(world_id=self.id)])

        if not self.session:
            return Err([world_errors.WorldStateStorageUnsupported(world_id=self.id)])

        path = self._journal_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("ab") as stream:
            stream.write(content.rstrip(b"\n"))
            stream.write(b"\n")

        return Ok(None)

    def _journal_read_all(self, path: pathlib.Path) -> list[bytes]:
        if not path.exists():
            return []

        with path.open("rb") as stream:
            return [line.rstrip(b"\n") for line in stream if line.strip()]

    def _journal_file_identity(self, path: pathlib.Path) -> tuple[int, int] | None:
        try:
            path_stat = path.stat()
        except FileNotFoundError:
            return None

        if not stat.S_ISREG(path_stat.st_mode):
            return None

        return (path_stat.st_dev, path_stat.st_ino)

    def _journal_follow(  # noqa: CCR001
        self,
        poll_interval: float = 0.25,
    ) -> Iterable[Result[bytes, ErrorsList]]:
        path = self._journal_path()

        stream = None
        stream_identity: tuple[int, int] | None = None

        # if the journal file did exist when we started following, we want to read from the end
        # if the journal file didn't exist when we started following, we want to read from the start
        start_from_head = False

        while True:
            file_identity = self._journal_file_identity(path)

            if stream is not None and stream_identity != file_identity:
                stream.close()
                stream = None
                stream_identity = None

            if file_identity is None or file_identity == stream_identity:
                start_from_head = True

            if stream is None and file_identity is not None:
                stream = path.open("rb")

                if not start_from_head:
                    stream.seek(0, os.SEEK_END)

                stream_identity = file_identity

            if stream is None:
                time.sleep(poll_interval)
                continue

            while line := stream.readline():
                line = line.rstrip(b"\n")
                if line.strip():
                    yield Ok(line)

            time.sleep(poll_interval)

    def _journal_read_some(self, lines: int | None = None) -> Iterable[Result[bytes, ErrorsList]]:
        path = self._journal_path()

        records = self._journal_read_all(path)

        if lines is not None:
            records = records[-lines:] if lines > 0 else []

        for record in records:
            yield Ok(record)

    def journal_read(self, lines: int | None = None, follow: bool = False) -> Iterable[Result[bytes, ErrorsList]]:
        if not self.session:
            yield Err([world_errors.WorldStateStorageUnsupported(world_id=self.id)])
            return

        yield from self._journal_read_some(lines=lines)

        if not follow:
            return

        yield from self._journal_follow()

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

        from donna.workspaces.config import project_dir

        path = pathlib.Path(path_value).expanduser()
        if not path.is_absolute():
            path = project_dir() / path

        return World(
            id=config.id,
            path=path.resolve(),
            readonly=config.readonly,
            session=config.session,
        )
