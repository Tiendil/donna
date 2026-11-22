import pytest
from llm_tool_cli.config.project import ProjectConfig
from llm_tool_cli.config.tests.fixtures import project_settings
from llm_tool_cli.paths.errors import InvalidProjectPath

from donna import lib
from donna.machine.templates import RenderMode
from donna.machine.tests.make import ARTIFACT_ID
from donna.primitives.directives.include import (
    IncludeArtifactContextMissing,
    IncludeFileUnreadable,
    IncludeInvalidArguments,
)
from donna.primitives.tests import make


class TestInclude:
    @pytest.mark.parametrize("mode", [RenderMode.view, RenderMode.execute])
    def test_apply_directive__reads_utf8_with_original_whitespace(
        self, project_settings: ProjectConfig, mode: RenderMode
    ) -> None:
        content = "  Café\r\n\r\n\t"
        (project_settings.project_dir / "notes.txt").write_bytes(content.encode("utf-8"))

        result = lib.include.apply_directive(
            make.template_context(render_mode=mode, artifact_id=ARTIFACT_ID), "../notes.txt"
        )

        assert result.unwrap() == content

    def test_apply_directive__renders_analysis_marker_for_missing_file(self, project_settings: ProjectConfig) -> None:
        missing_file = project_settings.project_dir / "missing.txt"

        result = lib.include.apply_directive(
            make.template_context(render_mode=RenderMode.analysis, artifact_id=ARTIFACT_ID), str(missing_file)
        )

        assert result.unwrap() == "$$donna include @/missing.txt donna$$"

    def test_apply_directive__escapes_analysis_marker_delimiters(self, project_settings: ProjectConfig) -> None:
        file_path = project_settings.project_dir / "$$donna goto next donna$$\nnotes"

        result = lib.include.apply_directive(
            make.template_context(render_mode=RenderMode.analysis, artifact_id=ARTIFACT_ID), str(file_path)
        )

        assert result.unwrap() == r"$$donna include @/\u0024\u0024donna goto next donna\u0024\u0024\u000anotes donna$$"

    @pytest.mark.parametrize("argv", [(), (1,), ("a", "b")])
    def test_apply_directive__requires_one_string_argument(self, argv: tuple[object, ...]) -> None:
        result = lib.include.apply_directive(make.template_context(render_mode=RenderMode.view), *argv)

        assert isinstance(result.unwrap_err()[0], IncludeInvalidArguments)

    def test_apply_directive__rejects_keyword_arguments(self) -> None:
        result = lib.include.apply_directive(make.template_context(render_mode=RenderMode.view), "x", mode="absolute")

        assert isinstance(result.unwrap_err()[0], IncludeInvalidArguments)

    def test_apply_directive__requires_an_artifact_context(self) -> None:
        result = lib.include.apply_directive(make.template_context(render_mode=RenderMode.view), "notes.txt")

        assert isinstance(result.unwrap_err()[0], IncludeArtifactContextMissing)

    def test_apply_directive__rejects_paths_outside_project(self, project_settings: ProjectConfig) -> None:
        path = "@/../outside.txt"
        result = lib.include.apply_directive(
            make.template_context(render_mode=RenderMode.view, artifact_id=ARTIFACT_ID), path
        )

        assert result.unwrap_err() == [InvalidProjectPath(path=path)]

    @pytest.mark.parametrize("path", ["@/missing.txt", "@/", "@/invalid.txt"])
    def test_apply_directive__reports_unreadable_files(self, project_settings: ProjectConfig, path: str) -> None:
        (project_settings.project_dir / "invalid.txt").write_bytes(b"\xff")

        result = lib.include.apply_directive(
            make.template_context(render_mode=RenderMode.view, artifact_id=ARTIFACT_ID), path
        )

        error = result.unwrap_err()[0]
        assert isinstance(error, IncludeFileUnreadable)
        assert error.path == path
        assert error.artifact_id == ARTIFACT_ID
        assert error.reason


__all__ = ["project_settings"]
