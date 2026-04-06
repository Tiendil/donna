import pathlib
import shutil
from typing import TYPE_CHECKING, cast

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.artifact_ids import ArtifactId, FullArtifactId, FullArtifactIdPattern
from donna.domain.types import Milliseconds
from donna.workspaces import errors as world_errors
from donna.workspaces.artifacts_discovery import ArtifactListingNode, list_artifacts_by_pattern
from donna.workspaces.worlds.base import RawArtifact
from donna.workspaces.worlds.base import World as BaseWorld

if TYPE_CHECKING:
    from donna.machine.artifacts import Artifact
    from donna.workspaces.artifacts import ArtifactRenderContext


class FilesystemRawArtifact(RawArtifact):
    path: pathlib.Path

    def get_bytes(self) -> bytes:
        return self.path.read_bytes()

    @unwrap_to_error
    def render(
        self, full_id: FullArtifactId, render_context: "ArtifactRenderContext"
    ) -> Result["Artifact", ErrorsList]:
        from donna.workspaces.config import config

        source_config = config().get_source_config(self.source_id).unwrap()
        return Ok(source_config.construct_artifact_from_bytes(full_id, self.get_bytes(), render_context).unwrap())


class World(BaseWorld):
    path: pathlib.Path

    def _artifact_listing_root(self) -> ArtifactListingNode | None:
        if not self.path.exists():
            return None

        return cast(ArtifactListingNode, self.path)

    def _resolve_artifact_file(self, artifact_id: ArtifactId) -> Result[pathlib.Path | None, ErrorsList]:
        artifact_path = self.path.joinpath(*artifact_id.parts)
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
            return Err([world_errors.ArtifactMultipleFiles(artifact_id=artifact_id)])

        return Ok(matches[0])

    def has(self, artifact_id: ArtifactId) -> bool:
        resolve_result = self._resolve_artifact_file(artifact_id)
        if resolve_result.is_err():
            return True

        return resolve_result.unwrap() is not None

    @unwrap_to_error
    def fetch(self, artifact_id: ArtifactId) -> Result[RawArtifact, ErrorsList]:
        path = self._resolve_artifact_file(artifact_id).unwrap()
        if path is None:
            return Err([world_errors.ArtifactNotFound(artifact_id=artifact_id)])

        from donna.workspaces.config import config

        source_config = config().find_source_for_extension(path.suffix)
        if source_config is None:
            return Err(
                [
                    world_errors.UnsupportedArtifactSourceExtension(
                        artifact_id=artifact_id,
                        extension=path.suffix,
                    )
                ]
            )

        return Ok(
            FilesystemRawArtifact(
                source_id=source_config.kind,
                path=path,
            )
        )

    @unwrap_to_error
    def has_artifact_changed(self, artifact_id: ArtifactId, since: Milliseconds) -> Result[bool, ErrorsList]:
        path = self._resolve_artifact_file(artifact_id).unwrap()

        if path is None:
            return Ok(True)

        return Ok((path.stat().st_mtime_ns // 1_000_000) > since)

    def list_artifacts(self, pattern: FullArtifactIdPattern) -> list[ArtifactId]:  # noqa: CCR001
        return list_artifacts_by_pattern(
            root=self._artifact_listing_root(),
            pattern=pattern,
        )

    @unwrap_to_error
    def initialize(self, reset: bool = False) -> Result[None, ErrorsList]:
        super().initialize(reset=reset).unwrap()

        if self.path.exists() and reset:
            shutil.rmtree(self.path)

        self.path.mkdir(parents=True, exist_ok=True)
        return Ok(None)

    def is_initialized(self) -> bool:
        return self.path.exists()
