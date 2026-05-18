from typing import TYPE_CHECKING

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.artifact_ids import ArtifactId
from donna.machine.artifacts import Artifact
from donna.machine.tasks import Task, WorkUnit
from donna.machine.templates import RenderMode
from donna.workspaces import errors as workspace_errors

if TYPE_CHECKING:
    from donna.workspaces.artifacts import ArtifactRenderContext, FilesystemRawArtifact
    from donna.workspaces.files import FileFingerprint


class _ArtifactCacheValue:
    __slots__ = ("fingerprint", "raw_artifact", "rendered_artifacts")

    def __init__(
        self,
        raw_artifact: "FilesystemRawArtifact",
        rendered_artifacts: dict[RenderMode, Artifact],
        fingerprint: "FileFingerprint",
    ) -> None:
        self.raw_artifact = raw_artifact
        self.rendered_artifacts = rendered_artifacts
        self.fingerprint = fingerprint


class ArtifactsCache:
    __slots__ = ("_cache",)

    def __init__(self) -> None:
        self._cache: dict[ArtifactId, _ArtifactCacheValue] = {}

    @unwrap_to_error
    def _is_cache_stale(self, artifact_id: ArtifactId, fingerprint: "FileFingerprint") -> Result[bool, ErrorsList]:
        from donna.workspaces.artifacts import artifact_fingerprint

        return Ok(artifact_fingerprint(artifact_id).unwrap() != fingerprint)

    @staticmethod
    @unwrap_to_error
    def _load_raw_artifact(artifact_id: ArtifactId) -> Result["FilesystemRawArtifact", ErrorsList]:
        from donna.workspaces.artifacts import fetch_raw_artifact

        return Ok(fetch_raw_artifact(artifact_id).unwrap())

    @unwrap_to_error
    def _refresh_cache_value(self, artifact_id: ArtifactId) -> Result[_ArtifactCacheValue, ErrorsList]:
        from donna.workspaces.files import FileFingerprint

        raw_artifact = self._load_raw_artifact(artifact_id).unwrap()
        fingerprint = FileFingerprint.from_path(raw_artifact.path)
        if fingerprint is None:
            return Err([workspace_errors.ArtifactNotFound(artifact_id=artifact_id)])

        refreshed = _ArtifactCacheValue(
            raw_artifact=raw_artifact,
            rendered_artifacts={},
            fingerprint=fingerprint,
        )
        self._cache[artifact_id] = refreshed
        return Ok(refreshed)

    @unwrap_to_error
    def _get_cache_value(self, artifact_id: ArtifactId) -> Result[_ArtifactCacheValue, ErrorsList]:
        cached = self._cache.get(artifact_id)

        if cached is None:
            return Ok(self._refresh_cache_value(artifact_id).unwrap())

        cache_stale = self._is_cache_stale(artifact_id, cached.fingerprint).unwrap()
        if not cache_stale:
            return Ok(cached)

        return Ok(self._refresh_cache_value(artifact_id).unwrap())

    def invalidate(self, artifact_id: ArtifactId) -> None:
        self._cache.pop(artifact_id, None)

    def load_for_view(self, artifact_id: ArtifactId) -> Result[Artifact, ErrorsList]:
        from donna.workspaces.artifacts import RENDER_CONTEXT_VIEW

        return self.load(artifact_id, RENDER_CONTEXT_VIEW)

    def load_for_execution(
        self,
        artifact_id: ArtifactId,
        task: Task,
        work_unit: WorkUnit,
    ) -> Result[Artifact, ErrorsList]:
        from donna.workspaces.artifacts import ArtifactRenderContext

        return self.load(
            artifact_id,
            ArtifactRenderContext(
                primary_mode=RenderMode.execute,
                current_task=task,
                current_work_unit=work_unit,
            ),
        )

    @unwrap_to_error
    def load(  # noqa: CCR001
        self,
        artifact_id: ArtifactId,
        render_context: "ArtifactRenderContext",
    ) -> Result[Artifact, ErrorsList]:
        cached = self._get_cache_value(artifact_id).unwrap()

        if render_context.primary_mode == RenderMode.execute:
            return Ok(cached.raw_artifact.render(artifact_id, render_context).unwrap())

        cached_artifact = cached.rendered_artifacts.get(render_context.primary_mode)
        if cached_artifact is not None:
            return Ok(cached_artifact)

        artifact = cached.raw_artifact.render(artifact_id, render_context).unwrap()
        cached.rendered_artifacts[render_context.primary_mode] = artifact

        return Ok(artifact)

    @unwrap_to_error
    def list(  # noqa: CCR001
        self,
        render_context: "ArtifactRenderContext",
    ) -> Result[list[Artifact], ErrorsList]:
        from donna.workspaces.artifacts import list_artifact_ids

        artifacts: list[Artifact] = []
        errors: ErrorsList = []

        for artifact_id in list_artifact_ids():
            artifact_result = self.load(artifact_id, render_context)

            if artifact_result.is_err():
                errors.extend(artifact_result.unwrap_err())
                continue

            artifact = artifact_result.unwrap()
            artifacts.append(artifact)

        if errors:
            return Err(errors)

        return Ok(artifacts)
