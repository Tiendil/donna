import pathlib

import pytest
from llm_tool_cli.config.project import ProjectConfig, project_config
from llm_tool_cli.config.tests.fixtures import project_settings
from llm_tool_cli.core.result import Err, Ok
from llm_tool_cli.paths import ProjectConfigPath, RelativeProjectPath, ResolvedProjectPath
from llm_tool_cli.paths.errors import FilesUnreadable, InvalidProjectPath, PathResolutionFailed
from pytest_mock import MockerFixture

from donna.domain.artifact_ids import ArtifactId
from donna.machine import ArtifactRenderContext
from donna.machine.artifacts import Artifact
from donna.machine.templates import RENDER_CONTEXT_VIEW, RenderMode
from donna.workspaces import artifacts
from donna.workspaces import config as workspace_config
from donna.workspaces import errors as workspace_errors
from donna.workspaces.config import Config
from donna.workspaces.files import FileFingerprint
from donna.workspaces.tests import make


class TestHasDonnaArtifactExtension:
    def test_matches_donna_markdown_suffix_case_insensitively(self) -> None:
        assert artifacts.has_donna_artifact_extension("workflow.donna.md")
        assert artifacts.has_donna_artifact_extension("workflow.DONNA.MD")
        assert not artifacts.has_donna_artifact_extension("workflow.md")


class TestArtifactRenderContext:
    def test_defaults__omit_current_work(self) -> None:
        context = ArtifactRenderContext(primary_mode=RenderMode.view)

        assert context.primary_mode == RenderMode.view
        assert context.current_task is None
        assert context.current_work_unit is None


class TestWorkflowDirParts:
    def test_returns_posix_parts(self) -> None:
        path = RelativeProjectPath(pathlib.Path("workflows") / "nested")

        assert artifacts._workflow_dir_parts(path) == ("workflows", "nested")


class TestArtifactIsInWorkflowDirs:
    def test_accepts_artifacts_under_configured_workflow_dirs(self) -> None:
        assert artifacts._artifact_is_in_workflow_dirs(
            make.ARTIFACT_ID,
            [RelativeProjectPath(pathlib.Path("workflows"))],
        )

    def test_rejects_workflow_dir_itself_and_other_dirs(self) -> None:
        assert not artifacts._artifact_is_in_workflow_dirs(
            ArtifactId("@/workflows.donna.md"),
            [RelativeProjectPath(pathlib.Path("workflows"))],
        )
        assert not artifacts._artifact_is_in_workflow_dirs(
            make.ARTIFACT_ID,
            [RelativeProjectPath(pathlib.Path("other"))],
        )


class TestArtifactIsVisibleInWorkspace:
    def test_uses_configured_workflow_dirs(self, mocker: MockerFixture) -> None:
        with workspace_config.config.scope(Config(workflow_dirs=[RelativeProjectPath(pathlib.Path("workflows"))])):

            assert artifacts._artifact_is_visible_in_workspace(make.ARTIFACT_ID)


class TestWalkFilesystem:
    def test_walk_filesystem__lists_artifacts_in_workflow_dirs(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        workflows = tmp_path / "workflows"
        nested = workflows / "nested"
        nested.mkdir(parents=True)
        (workflows / "b.donna.md").write_text("", encoding="utf-8")
        (workflows / "ignored.md").write_text("", encoding="utf-8")
        (workflows / "spaced name.donna.md").write_text("", encoding="utf-8")
        (nested / "a.donna.md").write_text("", encoding="utf-8")

        assert artifacts.walk_filesystem([RelativeProjectPath(pathlib.Path("workflows"))]).unwrap() == [
            ArtifactId("@/workflows/b.donna.md"),
            ArtifactId("@/workflows/nested/a.donna.md"),
            ArtifactId("@/workflows/spaced name.donna.md"),
        ]

    def test_walk_filesystem__preserves_workflow_dir_order(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        first = tmp_path / "first"
        second = tmp_path / "second"
        first.mkdir()
        second.mkdir()
        (first / "b.donna.md").write_text("", encoding="utf-8")
        (second / "a.donna.md").write_text("", encoding="utf-8")

        assert artifacts.walk_filesystem(
            [
                RelativeProjectPath(pathlib.Path("second")),
                RelativeProjectPath(pathlib.Path("first")),
            ]
        ).unwrap() == [
            ArtifactId("@/second/a.donna.md"),
            ArtifactId("@/first/b.donna.md"),
        ]

    def test_walk_filesystem__ignores_missing_workflow_dirs(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:

        assert artifacts.walk_filesystem([RelativeProjectPath(pathlib.Path("missing"))]).unwrap() == []

    def test_skips_discovered_links_and_preserves_hidden_uppercase_artifacts(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        directory = tmp_path / "workflows"
        directory.mkdir()
        (directory / ".hidden.DONNA.MD").touch()
        (directory / "file.donna.md").symlink_to(directory / ".hidden.DONNA.MD")
        (directory / "cycle").symlink_to(directory)
        (directory / "external").symlink_to(tmp_path.parent)

        assert artifacts.walk_filesystem([RelativeProjectPath(pathlib.Path("workflows"))]).unwrap() == [
            ArtifactId("@/workflows/.hidden.DONNA.MD")
        ]

    @pytest.mark.parametrize("name", ["link", "link/nested"])
    def test_rejects_configured_directory_through_link(
        self, mocker: MockerFixture, tmp_path: pathlib.Path, name: str
    ) -> None:
        (tmp_path / "link").symlink_to(tmp_path)

        assert artifacts.walk_filesystem([RelativeProjectPath(pathlib.Path(name))]).is_err(InvalidProjectPath)

    @pytest.mark.parametrize("name", [".", "[work]*?", "{*name}", "{**path}", "~", "@literal"])
    def test_preserves_literal_workflow_directory_names(
        self, mocker: MockerFixture, tmp_path: pathlib.Path, name: str
    ) -> None:
        directory = tmp_path / name
        directory.mkdir(exist_ok=True)
        (directory / "test.donna.md").touch()

        assert artifacts.walk_filesystem([RelativeProjectPath(pathlib.Path(name))]).unwrap() == [
            ArtifactId("@/" + (directory / "test.donna.md").relative_to(tmp_path).as_posix())
        ]


class TestListArtifactIds:
    def test_list_artifact_ids__deduplicates_discovered_artifacts(self, mocker: MockerFixture) -> None:
        config = Config(workflow_dirs=[RelativeProjectPath(pathlib.Path("workflows"))])
        with workspace_config.config.scope(config):
            mocker.patch.object(
                artifacts,
                "walk_filesystem",
                return_value=Ok([make.ARTIFACT_ID, make.ARTIFACT_ID, ArtifactId("@/workflows/other.donna.md")]),
            )

            assert artifacts.list_artifact_ids().unwrap() == [
                make.ARTIFACT_ID,
                ArtifactId("@/workflows/other.donna.md"),
            ]

    def test_propagates_directory_read_failure(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        (tmp_path / "workflows").mkdir()
        with workspace_config.config.scope(Config()):
            cause = PermissionError("cannot list directory")
            mocker.patch.object(pathlib.Path, "iterdir", side_effect=cause)

            failure = artifacts.list_artifact_ids().unwrap_err()[0]

            assert isinstance(failure, FilesUnreadable)
            assert failure.cause == cause


class TestResolveArtifactPath:
    @pytest.mark.parametrize("suffix", ["file.donna.md", "directory/file.donna.md"])
    def test_skips_internal_symlinks(self, mocker: MockerFixture, tmp_path: pathlib.Path, suffix: str) -> None:
        target = tmp_path / "real"
        target.mkdir()
        (target / "file.donna.md").touch()
        (tmp_path / "file.donna.md").symlink_to(target / "file.donna.md")
        (tmp_path / "directory").symlink_to(target)

        assert artifacts.resolve_artifact_path(ArtifactId("@/" + suffix)).unwrap() is None

    def test_resolve_artifact_path__preserves_resolution_failure(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        path = tmp_path / "workflows" / "test.donna.md"
        path.parent.mkdir()
        path.touch()
        cause = PermissionError("permission denied")
        resolve = pathlib.Path.resolve

        def fail_target(candidate: pathlib.Path) -> pathlib.Path:
            if candidate == path:
                raise cause
            return resolve(candidate)

        mocker.patch.object(pathlib.Path, "resolve", autospec=True, side_effect=fail_target)

        failures = artifacts.resolve_artifact_path(make.ARTIFACT_ID).unwrap_err()

        assert len(failures) == 1
        failure = failures[0]
        assert isinstance(failure, PathResolutionFailed)
        assert failure.code == "path_resolution_failed"
        assert failure.path == str(path)
        assert failure.cause == cause

    def test_resolve_artifact_path__skips_symlink_outside_project(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        project = tmp_path / "project"
        workflows = project / "workflows"
        workflows.mkdir(parents=True)
        outside = tmp_path / "outside.donna.md"
        outside.write_text("", encoding="utf-8")
        (workflows / "test.donna.md").symlink_to(outside)
        with project_config.scope(ProjectConfig(config_path=ProjectConfigPath(project / "donna.toml"))):
            result = artifacts.resolve_artifact_path(make.ARTIFACT_ID)

        assert result.is_ok()
        assert result.unwrap() is None

    def test_resolve_artifact_path__returns_existing_visible_file(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        path = tmp_path / "workflows" / "test.donna.md"
        path.parent.mkdir()
        path.write_text("", encoding="utf-8")

        result = artifacts.resolve_artifact_path(make.ARTIFACT_ID)

        assert result.is_ok()
        assert result.unwrap() == path

    def test_resolve_artifact_path__returns_none_for_missing_file(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:

        result = artifacts.resolve_artifact_path(make.ARTIFACT_ID)

        assert result.is_ok()
        assert result.unwrap() is None


class TestFilesystemRawArtifact:
    def test_get_bytes__returns_file_bytes(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "workflow.donna.md"
        path.write_bytes(b"content")
        raw_artifact = artifacts.FilesystemRawArtifact(path=ResolvedProjectPath(path))

        assert raw_artifact.get_bytes() == b"content"

    def test_render__renders_markdown_from_file_bytes(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "workflow.donna.md"
        path.write_bytes(b"# Workflow")
        expected_artifact = Artifact(id=make.ARTIFACT_ID, sections=[])
        render_markdown_artifact = mocker.patch.object(
            artifacts,
            "render_markdown_artifact",
            return_value=Ok(expected_artifact),
        )
        raw_artifact = artifacts.FilesystemRawArtifact(path=ResolvedProjectPath(path))

        result = raw_artifact.render(make.ARTIFACT_ID, RENDER_CONTEXT_VIEW)

        assert result.is_ok()
        assert result.unwrap() == expected_artifact
        render_markdown_artifact.assert_called_once_with(
            make.ARTIFACT_ID,
            b"# Workflow",
            RENDER_CONTEXT_VIEW,
        )

    def test_render__returns_markdown_render_errors(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "workflow.donna.md"
        path.write_bytes(b"# Workflow")
        error = workspace_errors.MarkdownArtifactWithoutSections(artifact_id=make.ARTIFACT_ID)
        mocker.patch.object(artifacts, "render_markdown_artifact", return_value=Err([error]))
        raw_artifact = artifacts.FilesystemRawArtifact(path=ResolvedProjectPath(path))

        result = raw_artifact.render(make.ARTIFACT_ID, RENDER_CONTEXT_VIEW)

        assert result.is_err()
        assert result.unwrap_err() == [error]


class TestFetchRawArtifact:
    def test_fetch_raw_artifact__returns_filesystem_artifact(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        path = tmp_path / "workflows" / "test.donna.md"
        path.parent.mkdir()
        path.write_text("content", encoding="utf-8")
        with workspace_config.config.scope(Config(workflow_dirs=[RelativeProjectPath(pathlib.Path("workflows"))])):

            result = artifacts.fetch_raw_artifact(make.ARTIFACT_ID)

            assert result.is_ok()
            assert result.unwrap().get_bytes() == b"content"

    def test_fetch_raw_artifact__rejects_artifacts_outside_workflow_dirs(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        with workspace_config.config.scope(Config(workflow_dirs=[RelativeProjectPath(pathlib.Path("other"))])):

            result = artifacts.fetch_raw_artifact(make.ARTIFACT_ID)

            assert result.is_err()
            assert isinstance(result.unwrap_err()[0], workspace_errors.ArtifactNotFound)


class TestFetchArtifactBytes:
    def test_fetch_artifact_bytes__returns_raw_bytes(self, mocker: MockerFixture) -> None:
        raw_artifact = mocker.Mock()
        raw_artifact.get_bytes.return_value = b"content"
        mocker.patch.object(artifacts, "fetch_raw_artifact", return_value=Ok(raw_artifact))

        result = artifacts.fetch_artifact_bytes(make.ARTIFACT_ID)

        assert result.is_ok()
        assert result.unwrap() == b"content"


class TestRenderMarkdownArtifact:
    def test_render_markdown_artifact__uses_workspace_defaults(self, mocker: MockerFixture) -> None:
        expected_artifact = Artifact(id=make.ARTIFACT_ID, sections=[])
        with workspace_config.config.scope(Config()):
            construct = mocker.patch(
                "donna.workspaces.markdown_parser.construct_artifact_from_bytes",
                return_value=Ok(expected_artifact),
            )

            result = artifacts.render_markdown_artifact(make.ARTIFACT_ID, b"# Workflow", RENDER_CONTEXT_VIEW)

            assert result.is_ok()
            assert result.unwrap() == expected_artifact
            construct.assert_called_once_with(
                make.ARTIFACT_ID,
                b"# Workflow",
                RENDER_CONTEXT_VIEW,
                default_section_kind=Config().defaults.tail_section_kind,
                default_primary_section_kind=Config().defaults.primary_section_kind,
                default_primary_section_id=Config().defaults.primary_section_id,
            )


class TestArtifactFingerprint:
    def test_artifact_fingerprint__returns_file_fingerprint(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        path = tmp_path / "workflow.donna.md"
        path.write_text("data", encoding="utf-8")
        mocker.patch.object(artifacts, "resolve_artifact_path", return_value=Ok(path))

        result = artifacts.artifact_fingerprint(make.ARTIFACT_ID)

        assert result.is_ok()
        assert result.unwrap() == FileFingerprint.from_path(path)

    def test_artifact_fingerprint__returns_none_for_missing_artifact(self, mocker: MockerFixture) -> None:
        mocker.patch.object(artifacts, "resolve_artifact_path", return_value=Ok(None))

        result = artifacts.artifact_fingerprint(make.ARTIFACT_ID)

        assert result.is_ok()
        assert result.unwrap() is None


__all__ = ["project_settings"]

pytestmark = pytest.mark.usefixtures("project_settings")
