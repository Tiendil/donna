import time
from pathlib import Path
from typing import TYPE_CHECKING

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import FullArtifactId, FullArtifactIdPattern, FullArtifactSectionId
from donna.machine.artifacts import Artifact, ArtifactSection
from donna.workspaces.templates import RenderMode

if TYPE_CHECKING:
    from donna.workspaces.artifacts import ArtifactRenderContext


class _ArtifactCacheValue:
    __slots__ = ("view_artifact", "analysis_artifact", "loaded_at_ms")

    def __init__(
        self,
        view_artifact: Artifact | None,
        analysis_artifact: Artifact | None,
        loaded_at_ms: int,
    ) -> None:
        self.view_artifact = view_artifact
        self.analysis_artifact = analysis_artifact
        self.loaded_at_ms = loaded_at_ms


class ArtifactsCache:
    __slots__ = ("_cache",)

    def __init__(self) -> None:
        self._cache: dict[FullArtifactId, _ArtifactCacheValue] = {}

    @staticmethod
    def _now_ms() -> int:
        return time.time_ns() // 1_000_000

    @staticmethod
    def _default_render_context() -> "ArtifactRenderContext":
        from donna.workspaces.artifacts import ArtifactRenderContext

        return ArtifactRenderContext(primary_mode=RenderMode.view)

    @staticmethod
    def _context_slot_name(render_context: "ArtifactRenderContext") -> str:
        if render_context.primary_mode == RenderMode.view:
            return "view_artifact"

        if render_context.primary_mode == RenderMode.analysis:
            return "analysis_artifact"

        return ""

    @unwrap_to_error
    def _is_cache_stale(self, full_id: FullArtifactId, loaded_at_ms: int) -> Result[bool, ErrorsList]:
        from donna.workspaces.config import config

        world = config().get_world(full_id.world_id).unwrap()
        return Ok(world.has_artifact_changed(full_id.artifact_id, since=loaded_at_ms).unwrap())

    def invalidate(self, full_id: FullArtifactId) -> None:
        self._cache.pop(full_id, None)

    @unwrap_to_error
    def load(  # noqa: CCR001
        self, full_id: FullArtifactId, render_context: "ArtifactRenderContext | None" = None
    ) -> Result[Artifact, ErrorsList]:
        from donna.workspaces import artifacts as workspace_artifacts

        if render_context is None:
            render_context = self._default_render_context()

        if render_context.primary_mode == RenderMode.execute:
            return Ok(workspace_artifacts.load_artifact(full_id, render_context).unwrap())

        cached = self._cache.get(full_id)
        cache_slot = self._context_slot_name(render_context)
        since = cached.loaded_at_ms if cached is not None else 0
        cache_stale = self._is_cache_stale(full_id, since).unwrap()

        if cached is not None and cache_slot:
            cached_artifact = getattr(cached, cache_slot)

            if cached_artifact is not None and not cache_stale:
                return Ok(cached_artifact)

        artifact = workspace_artifacts.load_artifact(full_id, render_context).unwrap()

        loaded_at_ms = self._now_ms()

        if cached is None:
            cached = _ArtifactCacheValue(view_artifact=None, analysis_artifact=None, loaded_at_ms=loaded_at_ms)
            self._cache[full_id] = cached
        else:
            cached.loaded_at_ms = loaded_at_ms

        if render_context.primary_mode == RenderMode.view:
            cached.view_artifact = artifact
        elif render_context.primary_mode == RenderMode.analysis:
            cached.analysis_artifact = artifact

        return Ok(artifact)

    @unwrap_to_error
    def resolve_section(
        self,
        target_id: FullArtifactSectionId,
        render_context: "ArtifactRenderContext | None" = None,
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
        render_context: "ArtifactRenderContext | None" = None,
        tags: list[str] | None = None,
    ) -> Result[list[Artifact], ErrorsList]:
        from donna.workspaces.config import config

        if render_context is None:
            render_context = self._default_render_context()

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
