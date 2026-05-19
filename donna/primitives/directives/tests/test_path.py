import pathlib

from pytest_mock import MockerFixture

from donna.domain.artifact_ids import ArtifactId
from donna.domain.paths import ProjectRootPath
from donna.machine.tests import make as machine_make
from donna.primitives.directives import path
from donna.primitives.directives.path import (
    Path,
    PathArtifactContextMissing,
    PathInvalidArguments,
    PathInvalidKeywordArguments,
    PathInvalidMode,
    PathNotProjectPath,
    PathRenderMode,
)
from donna.primitives.tests import make


class TestPath:
    def test_prepare_arguments__defaults_to_project_mode(self) -> None:
        result = Path(analyze_id="path")._prepare_arguments(
            make.template_context(artifact_id=machine_make.ARTIFACT_ID),
            "../specs/design.md",
        )

        assert result.is_ok()
        assert result.unwrap() == (
            "../specs/design.md",
            PathRenderMode.project,
            ArtifactId("@/workflows/test.donna.md"),
        )

    def test_prepare_arguments__accepts_absolute_mode(self) -> None:
        result = Path(analyze_id="path")._prepare_arguments(
            make.template_context(artifact_id=machine_make.ARTIFACT_ID),
            "@/README.md",
            mode="absolute",
        )

        assert result.is_ok()
        assert result.unwrap()[1] == PathRenderMode.absolute

    def test_prepare_arguments__requires_one_path_argument(self) -> None:
        result = Path(analyze_id="path")._prepare_arguments(
            make.template_context(artifact_id=machine_make.ARTIFACT_ID)
        )

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, PathInvalidArguments)
        assert error.provided_count == 0

    def test_prepare_arguments__rejects_unknown_keyword_arguments(self) -> None:
        result = Path(analyze_id="path")._prepare_arguments(
            make.template_context(artifact_id=machine_make.ARTIFACT_ID),
            "@/README.md",
            unknown=True,
        )

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, PathInvalidKeywordArguments)
        assert error.keywords == ["unknown"]

    def test_prepare_arguments__rejects_invalid_mode(self) -> None:
        result = Path(analyze_id="path")._prepare_arguments(
            make.template_context(artifact_id=machine_make.ARTIFACT_ID),
            "@/README.md",
            mode="host",
        )

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, PathInvalidMode)
        assert error.mode == "host"

    def test_prepare_arguments__requires_artifact_context(self) -> None:
        result = Path(analyze_id="path")._prepare_arguments(make.template_context(), "@/README.md")

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], PathArtifactContextMissing)

    def test_render_view__renders_project_root_anchored_path(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        mocker.patch.object(path.workspace_config, "project_dir", return_value=ProjectRootPath(tmp_path))

        result = Path(analyze_id="path").render_view(
            make.template_context(),
            "../specs/design.md",
            PathRenderMode.project,
            ArtifactId("@/workflows/rfc/design.donna.md"),
        )

        assert result.is_ok()
        assert result.unwrap() == "@/workflows/specs/design.md"

    def test_render_view__renders_absolute_path(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        mocker.patch.object(path.workspace_config, "project_dir", return_value=ProjectRootPath(tmp_path))

        result = Path(analyze_id="path").render_view(
            make.template_context(),
            "@/README.md",
            PathRenderMode.absolute,
            ArtifactId("@/workflows/rfc/design.donna.md"),
        )

        assert result.is_ok()
        assert result.unwrap() == str(tmp_path / "README.md")

    def test_render_view__accepts_absolute_input(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        mocker.patch.object(path.workspace_config, "project_dir", return_value=ProjectRootPath(tmp_path))
        absolute = tmp_path / "specs" / "design.md"

        result = Path(analyze_id="path").render_view(
            make.template_context(),
            str(absolute),
            PathRenderMode.project,
            ArtifactId("@/workflows/rfc/design.donna.md"),
        )

        assert result.is_ok()
        assert result.unwrap() == "@/specs/design.md"

    def test_render_view__rejects_paths_outside_project(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        mocker.patch.object(path.workspace_config, "project_dir", return_value=ProjectRootPath(tmp_path))

        result = Path(analyze_id="path").render_view(
            make.template_context(),
            "../../outside.md",
            PathRenderMode.project,
            ArtifactId("@/workflow.donna.md"),
        )

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, PathNotProjectPath)
        assert error.path == "../../outside.md"

    def test_render_analyze__renders_regular_path(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        mocker.patch.object(path.workspace_config, "project_dir", return_value=ProjectRootPath(tmp_path))

        result = Path(analyze_id="path").render_analyze(
            make.template_context(),
            "@/specs/design.md",
            PathRenderMode.project,
            ArtifactId("@/workflows/rfc/design.donna.md"),
        )

        assert result.is_ok()
        assert result.unwrap() == "@/specs/design.md"
