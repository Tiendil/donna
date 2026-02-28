from pathlib import Path
from typing import TYPE_CHECKING

from donna.context.entity_cache import TimedCache, TimedCacheValue
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import FullArtifactId, FullArtifactIdPattern, FullArtifactSectionId
from donna.domain.types import Milliseconds
from donna.machine.artifacts import Artifact, ArtifactSection
from donna.workspaces.templates import RenderMode

if TYPE_CHECKING:
    from donna.workspaces.artifacts import ArtifactRenderContext
    from donna.workspaces.worlds.base import RawArtifact


class _ArtifactCacheValue(TimedCacheValue):
    __slots__ = ("raw_artifact", "rendered_artifacts")

    def __init__(
        self,
        raw_artifact: "RawArtifact",
        rendered_artifacts: dict[RenderMode, Artifact],
        loaded_at_ms: Milliseconds,
        checked_at_ms: Milliseconds,
    ) -> None:
        super().__init__(loaded_at_ms=loaded_at_ms, checked_at_ms=checked_at_ms)
        self.raw_artifact = raw_artifact
        self.rendered_artifacts = rendered_artifacts


class ArtifactsCache(TimedCache):
    __slots__ = ("_cache",)

    def __init__(self) -> None:
        self._cache: dict[FullArtifactId, _ArtifactCacheValue] = {}

    @unwrap_to_error
    def _is_cache_stale(self, full_id: FullArtifactId, loaded_at_ms: Milliseconds) -> Result[bool, ErrorsList]:
        from donna.workspaces.config import config

        world = config().get_world(full_id.world_id).unwrap()
        return Ok(world.has_artifact_changed(full_id.artifact_id, since=loaded_at_ms).unwrap())

    @staticmethod
    @unwrap_to_error
    def _load_raw_artifact(full_id: FullArtifactId) -> Result["RawArtifact", ErrorsList]:
        from donna.workspaces.config import config

        world = config().get_world(full_id.world_id).unwrap()
        return Ok(world.fetch(full_id.artifact_id).unwrap())

    @unwrap_to_error
    def _refresh_cache_value(
        self, full_id: FullArtifactId, now_ms: Milliseconds
    ) -> Result[_ArtifactCacheValue, ErrorsList]:
        raw_artifact = self._load_raw_artifact(full_id).unwrap()
        refreshed = _ArtifactCacheValue(
            raw_artifact=raw_artifact,
            rendered_artifacts={},
            loaded_at_ms=now_ms,
            checked_at_ms=now_ms,
        )
        self._cache[full_id] = refreshed
        return Ok(refreshed)

    @unwrap_to_error
    def _get_cache_value(self, full_id: FullArtifactId) -> Result[_ArtifactCacheValue, ErrorsList]:
        cached = self._cache.get(full_id)
        now_ms = self._now_ms()

        if cached is None:
            return Ok(self._refresh_cache_value(full_id, now_ms).unwrap())

        # Skip expensive world checks when cache lifetime has not elapsed yet.
        if self._is_within_lifetime(cached, now_ms):
            return Ok(cached)

        cache_stale = self._is_cache_stale(full_id, cached.loaded_at_ms).unwrap()
        self._mark_checked(cached, now_ms)
        if not cache_stale:
            return Ok(cached)

        return Ok(self._refresh_cache_value(full_id, now_ms).unwrap())

    def invalidate(self, full_id: FullArtifactId) -> None:
        self._cache.pop(full_id, None)

    @unwrap_to_error
    def load(  # noqa: CCR001
        self,
        full_id: FullArtifactId,
        render_context: "ArtifactRenderContext",
    ) -> Result[Artifact, ErrorsList]:
        cached = self._get_cache_value(full_id).unwrap()

        if render_context.primary_mode == RenderMode.execute:
            return Ok(cached.raw_artifact.render(full_id, render_context).unwrap())

        cached_artifact = cached.rendered_artifacts.get(render_context.primary_mode)
        if cached_artifact is not None:
            return Ok(cached_artifact)

        artifact = cached.raw_artifact.render(full_id, render_context).unwrap()
        cached.rendered_artifacts[render_context.primary_mode] = artifact

        return Ok(artifact)

    @unwrap_to_error
    def resolve_section(
        self,
        target_id: FullArtifactSectionId,
        render_context: "ArtifactRenderContext",
    ) -> Result[ArtifactSection, ErrorsList]:
        artifact = self.load(target_id.full_artifact_id, render_context).unwrap()
        return Ok(artifact.get_section(target_id.local_id).unwrap())

    @unwrap_to_error
    def update(
        self,
        full_id: FullArtifactId,
        input_path: Path,
        extension: str | None = None,
    ) -> Result[None, ErrorsList]:
        from donna.workspaces import artifacts as workspace_artifacts

        workspace_artifacts.update_artifact(full_id, input_path, extension=extension).unwrap()
        self.invalidate(full_id)
        return Ok(None)

    @unwrap_to_error
    def copy(self, source_id: FullArtifactId, target_id: FullArtifactId) -> Result[None, ErrorsList]:
        from donna.workspaces import artifacts as workspace_artifacts

        workspace_artifacts.copy_artifact(source_id, target_id).unwrap()
        self.invalidate(target_id)
        return Ok(None)

    @unwrap_to_error
    def move(self, source_id: FullArtifactId, target_id: FullArtifactId) -> Result[None, ErrorsList]:
        from donna.workspaces import artifacts as workspace_artifacts

        workspace_artifacts.move_artifact(source_id, target_id).unwrap()
        self.invalidate(source_id)
        self.invalidate(target_id)
        return Ok(None)

    @unwrap_to_error
    def remove(self, full_id: FullArtifactId) -> Result[None, ErrorsList]:
        from donna.workspaces import artifacts as workspace_artifacts

        workspace_artifacts.remove_artifact(full_id).unwrap()
        self.invalidate(full_id)
        return Ok(None)

    @unwrap_to_error
    def file_extension(self, full_id: FullArtifactId) -> Result[str, ErrorsList]:
        from donna.workspaces import artifacts as workspace_artifacts

        return Ok(workspace_artifacts.artifact_file_extension(full_id).unwrap())

    @unwrap_to_error
    def fetch(self, full_id: FullArtifactId, output: Path) -> Result[None, ErrorsList]:
        from donna.workspaces import artifacts as workspace_artifacts

        workspace_artifacts.fetch_artifact(full_id, output).unwrap()
        return Ok(None)

    @unwrap_to_error
    def list(  # noqa: CCR001
        self,
        pattern: FullArtifactIdPattern,
        render_context: "ArtifactRenderContext",
        tags: list[str] | None = None,
    ) -> Result[list[Artifact], ErrorsList]:
        from donna.workspaces.config import config

        tag_filters = tags or []

        artifacts: list[Artifact] = []
        errors: ErrorsList = []

        for world in reversed(config().worlds_instances):
            for artifact_id in world.list_artifacts(pattern):
                full_id = FullArtifactId((world.id, artifact_id))
                artifact_result = self.load(full_id, render_context)
                if artifact_result.is_err():
                    errors.extend(artifact_result.unwrap_err())
                    continue

                artifact = artifact_result.unwrap()
                if tag_filters:
                    primary_result = artifact.primary_section()
                    if primary_result.is_err():
                        continue
                    primary = primary_result.unwrap()
                    if not all(tag in primary.tags for tag in tag_filters):
                        continue

                artifacts.append(artifact)

        if errors:
            return Err(errors)

        return Ok(artifacts)
