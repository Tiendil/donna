import pathlib

import pytest
from llm_tool_cli.paths import PathInput
from llm_tool_cli.paths.errors import InvalidProjectPath, PathResolutionFailed
from pytest_mock import MockerFixture

from donna.domain.artifact_ids import ArtifactId
from donna.domain.errors import InvalidIdFormat
from donna.workspaces.paths import (
    normalize_artifact_id,
    normalize_artifact_section_id,
    normalize_project_path,
)


class TestNormalizeProjectPath:
    @pytest.mark.parametrize("relative_to", [None, ArtifactId("@/workflows/source.donna.md")])
    def test_empty_input_propagates_shared_diagnostic(
        self, tmp_path: pathlib.Path, relative_to: ArtifactId | None
    ) -> None:
        result = normalize_project_path(
            "", PathInput(tmp_path), cwd=PathInput(tmp_path / "nested"), relative_to=relative_to
        )

        assert result.unwrap_err() == [InvalidProjectPath(path="")]

    @pytest.mark.parametrize("relative_to", [None, ArtifactId("@/workflows/source.donna.md")])
    def test_root_failure_precedes_empty_input_rejection(
        self, tmp_path: pathlib.Path, relative_to: ArtifactId | None
    ) -> None:
        root = tmp_path / "loop"
        root.symlink_to(root)

        failure = normalize_project_path("", PathInput(root), relative_to=relative_to).unwrap_err()[0]

        assert isinstance(failure, PathResolutionFailed)
        assert failure.code == "path_resolution_failed"
        assert failure.path == str(root)
        assert isinstance(failure.cause, (OSError, RuntimeError))

    @pytest.mark.parametrize("relative_to", [None, ArtifactId("@/workflows/source.donna.md")])
    def test_home_path_uses_shared_normalization(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, relative_to: ArtifactId | None
    ) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))

        assert (
            normalize_project_path("~/target.md", PathInput(tmp_path), relative_to=relative_to).unwrap()
            == "@/target.md"
        )

    @pytest.mark.parametrize("relative_to", [None, ArtifactId("@/workflows/source.donna.md")])
    def test_home_failure_propagates_shared_diagnostic(
        self, tmp_path: pathlib.Path, mocker: MockerFixture, relative_to: ArtifactId | None
    ) -> None:
        cause = RuntimeError("unknown home")
        mocker.patch.object(pathlib.Path, "expanduser", side_effect=cause)

        failure = normalize_project_path("~/target.md", PathInput(tmp_path), relative_to=relative_to).unwrap_err()[0]

        assert isinstance(failure, PathResolutionFailed)
        assert failure.path == "~/target.md"
        assert failure.cause == cause

    def test_normalizes_parent_relative_to_artifact_file(self, tmp_path: pathlib.Path) -> None:
        relative_to = ArtifactId("@/workflows/rfc/do.donna.md")

        assert (
            normalize_project_path("../plan.donna.md", PathInput(tmp_path), relative_to=relative_to).unwrap()
            == "@/workflows/plan.donna.md"
        )

    def test_uses_normalize_path_without_artifact_base(self, tmp_path: pathlib.Path) -> None:
        assert normalize_project_path("@/workflow.donna.md", PathInput(tmp_path)).unwrap() == "@/workflow.donna.md"

    def test_rejects_invalid_artifact_path(self, tmp_path: pathlib.Path) -> None:
        assert normalize_project_path(
            "../outside.donna.md", PathInput(tmp_path), relative_to=ArtifactId("@/file.donna.md")
        ).is_err()

        assert normalize_project_path(None, PathInput(tmp_path)).is_err()  # type: ignore[arg-type]

    def test_normalizes_relative_to_artifact_file(self, tmp_path: pathlib.Path) -> None:
        relative_to = ArtifactId("@/workflows/rfc/do.donna.md")

        assert normalize_project_path("specs/design.md", PathInput(tmp_path), relative_to=relative_to).unwrap() == (
            "@/workflows/rfc/specs/design.md"
        )

    def test_normalizes_absolute_path_when_artifact_base_is_present(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "specs" / "design.md"
        project_file.parent.mkdir()
        project_file.write_text("", encoding="utf-8")
        relative_to = ArtifactId("@/workflows/rfc/do.donna.md")

        assert (
            normalize_project_path(str(project_file), PathInput(tmp_path), relative_to=relative_to).unwrap()
            == "@/specs/design.md"
        )

    def test_accepts_project_paths_with_non_workflow_extensions(self, tmp_path: pathlib.Path) -> None:
        assert normalize_project_path("@/specs/design.md", PathInput(tmp_path)).unwrap() == "@/specs/design.md"

    def test_accepts_project_paths_without_suffixes(self, tmp_path: pathlib.Path) -> None:
        assert normalize_project_path("@/workflows", PathInput(tmp_path)).unwrap() == "@/workflows"
        assert normalize_project_path("@/README", PathInput(tmp_path)).unwrap() == "@/README"


class TestNormalizeArtifactId:
    def test_propagates_shared_path_error(self, tmp_path: pathlib.Path) -> None:
        result = normalize_artifact_id("@/../workflow.donna.md", PathInput(tmp_path))

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], InvalidProjectPath)

    def test_returns_artifact_id_for_valid_path(self, tmp_path: pathlib.Path) -> None:
        assert normalize_artifact_id("@/workflow.donna.md", PathInput(tmp_path)).unwrap() == ArtifactId(
            "@/workflow.donna.md"
        )

    def test_returns_artifact_id_for_relative_path_from_cwd(self, tmp_path: pathlib.Path) -> None:
        cwd = tmp_path / "workflows"
        cwd.mkdir()

        assert normalize_artifact_id("test.donna.md", PathInput(tmp_path), cwd=PathInput(cwd)).unwrap() == ArtifactId(
            "@/workflows/test.donna.md"
        )

    def test_rejects_invalid_artifact_id_path(self, tmp_path: pathlib.Path) -> None:
        for value in ("@/workflow", "@/workflow.md"):
            result = normalize_artifact_id(value, PathInput(tmp_path))

            assert result.is_err()
            assert isinstance(result.unwrap_err()[0], InvalidIdFormat)


class TestNormalizeArtifactSectionId:
    def test_propagates_shared_path_error(self, tmp_path: pathlib.Path) -> None:
        value = "@/../workflow.donna.md"
        result = normalize_artifact_section_id(value + ":step", PathInput(tmp_path))

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, InvalidProjectPath)
        assert error.path == value

    def test_returns_artifact_section_id_for_valid_input(self, tmp_path: pathlib.Path) -> None:
        assert (
            normalize_artifact_section_id("@/workflow.donna.md:step", PathInput(tmp_path)).unwrap()
            == "@/workflow.donna.md:step"
        )

    def test_returns_artifact_section_id_relative_to_artifact_file(self, tmp_path: pathlib.Path) -> None:
        relative_to = ArtifactId("@/workflows/rfc/do.donna.md")

        assert (
            normalize_artifact_section_id(
                "../plan.donna.md:step", PathInput(tmp_path), relative_to=relative_to
            ).unwrap()
            == "@/workflows/plan.donna.md:step"
        )

    @pytest.mark.parametrize("value", ["", "@/workflow.donna.md", "@/workflow.donna.md:---", "@/workflow.md:step"])
    def test_rejects_missing_or_invalid_section(self, tmp_path: pathlib.Path, value: str) -> None:
        result = normalize_artifact_section_id(value, PathInput(tmp_path))

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], InvalidIdFormat)
