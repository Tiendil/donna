import pathlib

from donna.core.result import Err, Ok
from donna.domain.artifact_ids import ArtifactId
from donna.domain.paths import RelativeProjectPath, ResolvedProjectPath
from donna.machine.artifacts import Artifact
from donna.workspaces import artifacts
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
        context = artifacts.ArtifactRenderContext(primary_mode=artifacts.RenderMode.view)

        assert context.primary_mode == artifacts.RenderMode.view
        assert context.current_task is None
        assert context.current_work_unit is None


class TestArtifactIdFromParts:
    def test_returns_artifact_id_for_valid_parts(self) -> None:
        assert artifacts._artifact_id_from_parts(["workflows", "test.donna.md"]) == make.ARTIFACT_ID

    def test_returns_none_for_invalid_parts(self) -> None:
        assert artifacts._artifact_id_from_parts(["invalid name.donna.md"]) is None


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
    def test_uses_configured_workflow_dirs(self, mocker: object) -> None:
        mocker.patch("donna.workspaces.config.config", return_value=Config(workflow_dirs=["workflows"]))

        assert artifacts._artifact_is_visible_in_workspace(make.ARTIFACT_ID)


class TestArtifactIdFromFilesystemEntry:
    def test_returns_artifact_id_for_regular_donna_file(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "test.donna.md"
        path.write_text("", encoding="utf-8")

        assert (
            artifacts._artifact_id_from_filesystem_entry(ResolvedProjectPath(path), ["workflows"]) == make.ARTIFACT_ID
        )

    def test_returns_none_for_dirs_non_artifacts_and_invalid_names(self, tmp_path: pathlib.Path) -> None:
        directory = tmp_path / "directory"
        directory.mkdir()
        ordinary_markdown = tmp_path / "ordinary.md"
        ordinary_markdown.write_text("", encoding="utf-8")
        invalid_name = tmp_path / "invalid name.donna.md"
        invalid_name.write_text("", encoding="utf-8")

        assert artifacts._artifact_id_from_filesystem_entry(ResolvedProjectPath(directory), ["workflows"]) is None
        assert (
            artifacts._artifact_id_from_filesystem_entry(ResolvedProjectPath(ordinary_markdown), ["workflows"]) is None
        )
        assert artifacts._artifact_id_from_filesystem_entry(ResolvedProjectPath(invalid_name), ["workflows"]) is None


class TestWalkWorkflowDir:
    def test_walks_directory_recursively_in_name_order(self, tmp_path: pathlib.Path) -> None:
        nested = tmp_path / "nested"
        nested.mkdir()
        (tmp_path / "b.donna.md").write_text("", encoding="utf-8")
        (nested / "a.donna.md").write_text("", encoding="utf-8")

        assert list(artifacts._walk_workflow_dir(ResolvedProjectPath(tmp_path), ["workflows"])) == [
            ArtifactId("@/workflows/b.donna.md"),
            ArtifactId("@/workflows/nested/a.donna.md"),
        ]


class TestWalkFilesystem:
    def test_walk_filesystem__lists_artifacts_in_workflow_dirs(self, mocker: object, tmp_path: pathlib.Path) -> None:
        workflows = tmp_path / "workflows"
        nested = workflows / "nested"
        nested.mkdir(parents=True)
        (workflows / "b.donna.md").write_text("", encoding="utf-8")
        (workflows / "ignored.md").write_text("", encoding="utf-8")
        (workflows / "invalid name.donna.md").write_text("", encoding="utf-8")
        (nested / "a.donna.md").write_text("", encoding="utf-8")
        mocker.patch("donna.workspaces.config.project_dir", return_value=tmp_path)

        assert list(artifacts.walk_filesystem([RelativeProjectPath(pathlib.Path("workflows"))])) == [
            ArtifactId("@/workflows/b.donna.md"),
            ArtifactId("@/workflows/nested/a.donna.md"),
        ]

    def test_walk_filesystem__preserves_workflow_dir_order(self, mocker: object, tmp_path: pathlib.Path) -> None:
        first = tmp_path / "first"
        second = tmp_path / "second"
        first.mkdir()
        second.mkdir()
        (first / "b.donna.md").write_text("", encoding="utf-8")
        (second / "a.donna.md").write_text("", encoding="utf-8")
        mocker.patch("donna.workspaces.config.project_dir", return_value=tmp_path)

        assert list(
            artifacts.walk_filesystem(
                [
                    RelativeProjectPath(pathlib.Path("second")),
                    RelativeProjectPath(pathlib.Path("first")),
                ]
            )
        ) == [
            ArtifactId("@/second/a.donna.md"),
            ArtifactId("@/first/b.donna.md"),
        ]

    def test_walk_filesystem__ignores_missing_workflow_dirs(self, mocker: object, tmp_path: pathlib.Path) -> None:
        mocker.patch("donna.workspaces.config.project_dir", return_value=tmp_path)

        assert list(artifacts.walk_filesystem([RelativeProjectPath(pathlib.Path("missing"))])) == []


class TestListArtifactIds:
    def test_list_artifact_ids__deduplicates_discovered_artifacts(self, mocker: object) -> None:
        config = Config(workflow_dirs=["workflows"])
        mocker.patch("donna.workspaces.config.config", return_value=config)
        mocker.patch.object(
            artifacts,
            "walk_filesystem",
            return_value=iter([make.ARTIFACT_ID, make.ARTIFACT_ID, ArtifactId("@/workflows/other.donna.md")]),
        )

        assert artifacts.list_artifact_ids() == [make.ARTIFACT_ID, ArtifactId("@/workflows/other.donna.md")]


class TestResolveArtifactPath:
    def test_resolve_artifact_path__returns_existing_visible_file(
        self, mocker: object, tmp_path: pathlib.Path
    ) -> None:
        path = tmp_path / "workflows" / "test.donna.md"
        path.parent.mkdir()
        path.write_text("", encoding="utf-8")
        mocker.patch("donna.workspaces.config.project_dir", return_value=tmp_path)

        result = artifacts.resolve_artifact_path(make.ARTIFACT_ID)

        assert result.is_ok()
        assert result.unwrap() == path

    def test_resolve_artifact_path__returns_none_for_missing_file(
        self, mocker: object, tmp_path: pathlib.Path
    ) -> None:
        mocker.patch("donna.workspaces.config.project_dir", return_value=tmp_path)

        result = artifacts.resolve_artifact_path(make.ARTIFACT_ID)

        assert result.is_ok()
        assert result.unwrap() is None


class TestFilesystemRawArtifact:
    def test_get_bytes__returns_file_bytes(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "workflow.donna.md"
        path.write_bytes(b"content")
        raw_artifact = artifacts.FilesystemRawArtifact(path=ResolvedProjectPath(path))

        assert raw_artifact.get_bytes() == b"content"

    def test_render__renders_markdown_from_file_bytes(self, mocker: object, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "workflow.donna.md"
        path.write_bytes(b"# Workflow")
        expected_artifact = Artifact(id=make.ARTIFACT_ID, sections=[])
        render_markdown_artifact = mocker.patch.object(
            artifacts,
            "render_markdown_artifact",
            return_value=Ok(expected_artifact),
        )
        raw_artifact = artifacts.FilesystemRawArtifact(path=ResolvedProjectPath(path))

        result = raw_artifact.render(make.ARTIFACT_ID, artifacts.RENDER_CONTEXT_VIEW)

        assert result.is_ok()
        assert result.unwrap() == expected_artifact
        render_markdown_artifact.assert_called_once_with(
            make.ARTIFACT_ID,
            b"# Workflow",
            artifacts.RENDER_CONTEXT_VIEW,
        )

    def test_render__returns_markdown_render_errors(self, mocker: object, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "workflow.donna.md"
        path.write_bytes(b"# Workflow")
        error = workspace_errors.MarkdownArtifactWithoutSections(artifact_id=make.ARTIFACT_ID)
        mocker.patch.object(artifacts, "render_markdown_artifact", return_value=Err([error]))
        raw_artifact = artifacts.FilesystemRawArtifact(path=ResolvedProjectPath(path))

        result = raw_artifact.render(make.ARTIFACT_ID, artifacts.RENDER_CONTEXT_VIEW)

        assert result.is_err()
        assert result.unwrap_err() == [error]


class TestFetchRawArtifact:
    def test_fetch_raw_artifact__returns_filesystem_artifact(self, mocker: object, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "workflows" / "test.donna.md"
        path.parent.mkdir()
        path.write_text("content", encoding="utf-8")
        mocker.patch("donna.workspaces.config.project_dir", return_value=tmp_path)
        mocker.patch("donna.workspaces.config.config", return_value=Config(workflow_dirs=["workflows"]))

        result = artifacts.fetch_raw_artifact(make.ARTIFACT_ID)

        assert result.is_ok()
        assert result.unwrap().get_bytes() == b"content"

    def test_fetch_raw_artifact__rejects_artifacts_outside_workflow_dirs(
        self, mocker: object, tmp_path: pathlib.Path
    ) -> None:
        mocker.patch("donna.workspaces.config.config", return_value=Config(workflow_dirs=["other"]))

        result = artifacts.fetch_raw_artifact(make.ARTIFACT_ID)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], workspace_errors.ArtifactNotFound)

    def test_fetch_raw_artifact__rejects_unsupported_artifact_extension(
        self, mocker: object, tmp_path: pathlib.Path
    ) -> None:
        artifact_id = ArtifactId("@/workflows/test.md")
        path = tmp_path / "workflows" / "test.md"
        path.parent.mkdir()
        path.write_text("content", encoding="utf-8")
        mocker.patch("donna.workspaces.config.project_dir", return_value=tmp_path)
        mocker.patch("donna.workspaces.config.config", return_value=Config(workflow_dirs=["workflows"]))

        result = artifacts.fetch_raw_artifact(artifact_id)

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.UnsupportedArtifactExtension)
        assert error.extension == ".md"


class TestFetchArtifactBytes:
    def test_fetch_artifact_bytes__returns_raw_bytes(self, mocker: object) -> None:
        raw_artifact = mocker.Mock()
        raw_artifact.get_bytes.return_value = b"content"
        mocker.patch.object(artifacts, "fetch_raw_artifact", return_value=Ok(raw_artifact))

        result = artifacts.fetch_artifact_bytes(make.ARTIFACT_ID)

        assert result.is_ok()
        assert result.unwrap() == b"content"


class TestRenderMarkdownArtifact:
    def test_render_markdown_artifact__uses_workspace_defaults(self, mocker: object) -> None:
        expected_artifact = Artifact(id=make.ARTIFACT_ID, sections=[])
        mocker.patch("donna.workspaces.config.config", return_value=Config())
        construct = mocker.patch(
            "donna.workspaces.markdown_parser.construct_artifact_from_bytes",
            return_value=Ok(expected_artifact),
        )

        result = artifacts.render_markdown_artifact(make.ARTIFACT_ID, b"# Workflow", artifacts.RENDER_CONTEXT_VIEW)

        assert result.is_ok()
        assert result.unwrap() == expected_artifact
        construct.assert_called_once_with(
            make.ARTIFACT_ID,
            b"# Workflow",
            artifacts.RENDER_CONTEXT_VIEW,
            default_section_kind=Config().defaults.tail_section_kind,
            default_primary_section_kind=Config().defaults.primary_section_kind,
            default_primary_section_id=Config().defaults.primary_section_id,
        )


class TestArtifactFingerprint:
    def test_artifact_fingerprint__returns_file_fingerprint(self, mocker: object, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "workflow.donna.md"
        path.write_text("data", encoding="utf-8")
        mocker.patch.object(artifacts, "resolve_artifact_path", return_value=Ok(path))

        result = artifacts.artifact_fingerprint(make.ARTIFACT_ID)

        assert result.is_ok()
        assert result.unwrap() == FileFingerprint.from_path(path)

    def test_artifact_fingerprint__returns_none_for_missing_artifact(self, mocker: object) -> None:
        mocker.patch.object(artifacts, "resolve_artifact_path", return_value=Ok(None))

        result = artifacts.artifact_fingerprint(make.ARTIFACT_ID)

        assert result.is_ok()
        assert result.unwrap() is None
