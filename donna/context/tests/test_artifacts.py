import pathlib

from pytest_mock import MockerFixture

from donna.context.artifacts import ArtifactsCache
from donna.context.tests import make
from donna.core.result import Ok
from donna.domain.artifact_ids import ArtifactId
from donna.machine.templates import RenderMode
from donna.machine.tests import make as machine_make
from donna.workspaces import artifacts as workspace_artifacts
from donna.workspaces import errors as workspace_errors
from donna.workspaces.files import FileFingerprint


def _write_artifact_file(tmp_path: pathlib.Path, name: str, content: str) -> pathlib.Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


class TestArtifactsCache:
    def test_load__caches_view_rendered_artifact_by_render_mode(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        path = _write_artifact_file(tmp_path, "workflow.donna.md", "# Workflow")
        raw_artifact = make.FakeRawArtifact(path, machine_make.artifact())
        mocker.patch("donna.workspaces.artifacts.fetch_raw_artifact", return_value=Ok(raw_artifact))
        mocker.patch(
            "donna.workspaces.artifacts.artifact_fingerprint", return_value=Ok(FileFingerprint.from_path(path))
        )
        cache = ArtifactsCache()

        first_result = cache.load(machine_make.ARTIFACT_ID, workspace_artifacts.RENDER_CONTEXT_VIEW)
        second_result = cache.load(machine_make.ARTIFACT_ID, workspace_artifacts.RENDER_CONTEXT_VIEW)

        assert first_result.is_ok()
        assert second_result.is_ok()
        assert first_result.unwrap() == second_result.unwrap()
        assert raw_artifact.render_modes == [RenderMode.view]

    def test_load__renders_execute_mode_every_time(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        path = _write_artifact_file(tmp_path, "workflow.donna.md", "# Workflow")
        raw_artifact = make.FakeRawArtifact(path, machine_make.artifact())
        mocker.patch("donna.workspaces.artifacts.fetch_raw_artifact", return_value=Ok(raw_artifact))
        mocker.patch(
            "donna.workspaces.artifacts.artifact_fingerprint", return_value=Ok(FileFingerprint.from_path(path))
        )
        render_context = workspace_artifacts.ArtifactRenderContext(primary_mode=RenderMode.execute)
        cache = ArtifactsCache()

        assert cache.load(machine_make.ARTIFACT_ID, render_context).is_ok()
        assert cache.load(machine_make.ARTIFACT_ID, render_context).is_ok()

        assert raw_artifact.render_modes == [RenderMode.execute, RenderMode.execute]

    def test_load__refreshes_stale_raw_artifact(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        first_path = _write_artifact_file(tmp_path, "first.donna.md", "# First")
        second_path = _write_artifact_file(tmp_path, "second.donna.md", "# Second with changed size")
        first_raw_artifact = make.FakeRawArtifact(first_path, machine_make.artifact())
        second_raw_artifact = make.FakeRawArtifact(second_path, machine_make.artifact())
        mocker.patch(
            "donna.workspaces.artifacts.fetch_raw_artifact",
            side_effect=[Ok(first_raw_artifact), Ok(second_raw_artifact)],
        )
        mocker.patch(
            "donna.workspaces.artifacts.artifact_fingerprint",
            return_value=Ok(FileFingerprint.from_path(second_path)),
        )
        cache = ArtifactsCache()

        assert cache.load(machine_make.ARTIFACT_ID, workspace_artifacts.RENDER_CONTEXT_VIEW).is_ok()
        result = cache.load(machine_make.ARTIFACT_ID, workspace_artifacts.RENDER_CONTEXT_VIEW)

        assert result.is_ok()
        assert first_raw_artifact.render_modes == [RenderMode.view]
        assert second_raw_artifact.render_modes == [RenderMode.view]

    def test_load__reports_missing_artifact_after_fetch(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        missing_path = tmp_path / "missing.donna.md"
        raw_artifact = make.FakeRawArtifact(missing_path, machine_make.artifact())
        mocker.patch("donna.workspaces.artifacts.fetch_raw_artifact", return_value=Ok(raw_artifact))

        result = ArtifactsCache().load(machine_make.ARTIFACT_ID, workspace_artifacts.RENDER_CONTEXT_VIEW)

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.ArtifactNotFound)
        assert error.artifact_id == machine_make.ARTIFACT_ID

    def test_invalidate__removes_cached_rendered_artifact(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        path = _write_artifact_file(tmp_path, "workflow.donna.md", "# Workflow")
        raw_artifact = make.FakeRawArtifact(path, machine_make.artifact())
        mocker.patch("donna.workspaces.artifacts.fetch_raw_artifact", return_value=Ok(raw_artifact))
        mocker.patch(
            "donna.workspaces.artifacts.artifact_fingerprint", return_value=Ok(FileFingerprint.from_path(path))
        )
        cache = ArtifactsCache()
        assert cache.load(machine_make.ARTIFACT_ID, workspace_artifacts.RENDER_CONTEXT_VIEW).is_ok()

        cache.invalidate(machine_make.ARTIFACT_ID)
        assert cache.load(machine_make.ARTIFACT_ID, workspace_artifacts.RENDER_CONTEXT_VIEW).is_ok()

        assert raw_artifact.render_modes == [RenderMode.view, RenderMode.view]

    def test_list__returns_loaded_artifacts_in_workspace_order(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        first_id = machine_make.ARTIFACT_ID
        second_id = ArtifactId("@/workflows/other.donna.md")
        first_path = _write_artifact_file(tmp_path, "first.donna.md", "# First")
        second_path = _write_artifact_file(tmp_path, "second.donna.md", "# Second")
        first_artifact = machine_make.artifact()
        second_artifact = machine_make.artifact().replace(id=second_id)
        mocker.patch("donna.workspaces.artifacts.list_artifact_ids", return_value=[first_id, second_id])
        mocker.patch(
            "donna.workspaces.artifacts.fetch_raw_artifact",
            side_effect=[
                Ok(make.FakeRawArtifact(first_path, first_artifact)),
                Ok(make.FakeRawArtifact(second_path, second_artifact)),
            ],
        )

        result = ArtifactsCache().list(workspace_artifacts.RENDER_CONTEXT_VIEW)

        assert result.is_ok()
        assert result.unwrap() == [first_artifact, second_artifact]

    def test_list__collects_artifact_loading_errors(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        missing_id = ArtifactId("@/workflows/missing.donna.md")
        path = _write_artifact_file(tmp_path, "workflow.donna.md", "# Workflow")
        mocker.patch(
            "donna.workspaces.artifacts.list_artifact_ids", return_value=[machine_make.ARTIFACT_ID, missing_id]
        )
        mocker.patch(
            "donna.workspaces.artifacts.fetch_raw_artifact",
            side_effect=[
                Ok(make.FakeRawArtifact(path, machine_make.artifact())),
                Ok(make.FakeRawArtifact(tmp_path / "missing.donna.md", machine_make.artifact())),
            ],
        )

        result = ArtifactsCache().list(workspace_artifacts.RENDER_CONTEXT_VIEW)

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.ArtifactNotFound)
        assert error.artifact_id == missing_id
