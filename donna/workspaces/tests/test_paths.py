import pathlib

import pytest
from llm_tool_cli.paths.errors import InvalidProjectPath

from donna.domain.artifact_ids import ArtifactId
from donna.domain.errors import InvalidIdFormat
from donna.domain.paths import ProjectRootPath, ResolvedProjectPath, UntrustedPath
from donna.workspaces import paths
from donna.workspaces.paths import (
    normalize_artifact_id,
    normalize_artifact_section_id,
    normalize_existing_path,
    normalize_path,
    normalize_project_path,
    resolve_project_path,
    resolve_project_root,
)


class TestResolveProjectRoot:
    def test_returns_resolved_root_path(self, tmp_path: pathlib.Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        root = project / ".." / "project"

        assert resolve_project_root(UntrustedPath(root)) == project


class TestResolveInsideProject:
    def test_returns_resolved_project_path_inside_root(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflow.donna.md"
        project_file.write_text("", encoding="utf-8")

        assert paths._resolve_inside_project(
            UntrustedPath(project_file),
            ProjectRootPath(tmp_path),
        ).unwrap() == ResolvedProjectPath(project_file)

    def test_rejects_project_root_and_outside_paths(self, tmp_path: pathlib.Path) -> None:
        assert paths._resolve_inside_project(UntrustedPath(tmp_path), ProjectRootPath(tmp_path)).is_err()
        assert paths._resolve_inside_project(UntrustedPath(tmp_path.parent), ProjectRootPath(tmp_path)).is_err()


class TestCanonicalFromResolved:
    def test_returns_canonical_path_for_valid_resolved_path(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflow.donna.md"

        assert (
            paths._canonical_from_resolved(ResolvedProjectPath(project_file), ProjectRootPath(tmp_path)).unwrap()
            == "@/workflow.donna.md"
        )

    def test_returns_canonical_path_for_filesystem_like_path(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "project plan.donna.md"

        assert (
            paths._canonical_from_resolved(ResolvedProjectPath(project_file), ProjectRootPath(tmp_path)).unwrap()
            == "@/project plan.donna.md"
        )

    def test_returns_canonical_path_for_suffixless_path(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "README"

        assert (
            paths._canonical_from_resolved(ResolvedProjectPath(project_file), ProjectRootPath(tmp_path)).unwrap()
            == "@/README"
        )

    def test_returns_canonical_path_for_directory_path(self, tmp_path: pathlib.Path) -> None:
        project_dir = tmp_path / "workflows"

        assert (
            paths._canonical_from_resolved(ResolvedProjectPath(project_dir), ProjectRootPath(tmp_path)).unwrap()
            == "@/workflows"
        )


class TestResolveRootAnchoredPath:
    def test_resolves_root_anchored_path_inside_project(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflow.donna.md"
        project_file.write_text("", encoding="utf-8")

        assert (
            paths._resolve_root_anchored_path("@/workflow.donna.md", ProjectRootPath(tmp_path)).unwrap()
            == project_file
        )

    def test_resolves_filesystem_like_root_anchored_path(self, tmp_path: pathlib.Path) -> None:
        assert (
            paths._resolve_root_anchored_path("@/project plan.donna.md", ProjectRootPath(tmp_path)).unwrap()
            == tmp_path / "project plan.donna.md"
        )

    def test_rejects_invalid_root_anchored_path(self, tmp_path: pathlib.Path) -> None:
        assert paths._resolve_root_anchored_path("@/../outside.donna.md", ProjectRootPath(tmp_path)).is_err()


class TestResolveProjectPath:
    def test_resolves_root_anchored_path_inside_project(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflows" / "test.donna.md"
        project_file.parent.mkdir()
        project_file.write_text("", encoding="utf-8")

        assert resolve_project_path("@/workflows/test.donna.md", tmp_path).unwrap() == project_file

    def test_resolves_absolute_path_inside_project(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflows" / "test.donna.md"
        project_file.parent.mkdir()
        project_file.write_text("", encoding="utf-8")

        assert resolve_project_path(str(project_file), tmp_path).unwrap() == project_file

    def test_rejects_root_escape_and_project_root(self, tmp_path: pathlib.Path) -> None:
        assert resolve_project_path("@/../outside.donna.md", tmp_path).is_err()
        assert resolve_project_path("@/.", tmp_path).is_err()

    def test_rejects_absolute_path_when_not_allowed(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflow.donna.md"
        project_file.write_text("", encoding="utf-8")

        assert resolve_project_path(str(project_file), tmp_path, allow_absolute=False).is_err()


class TestNormalizePath:
    def test_propagates_shared_lexical_error(self, tmp_path: pathlib.Path) -> None:
        value = "@/workflows//test.donna.md"
        result = normalize_path(value, tmp_path)

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, InvalidProjectPath)
        assert error.path == value

    def test_root_anchored_normalization_does_not_follow_symlinks(self, tmp_path: pathlib.Path) -> None:
        (tmp_path / "outside").symlink_to(tmp_path.parent, target_is_directory=True)

        assert normalize_path("@/outside/workflow.donna.md", tmp_path).unwrap() == "@/outside/workflow.donna.md"
        assert resolve_project_path("@/outside/workflow.donna.md", tmp_path).is_err()

    def test_normalizes_root_anchored_path(self, tmp_path: pathlib.Path) -> None:
        assert (
            normalize_path("@/workflows/./nested/../test.donna.md", tmp_path).unwrap() == "@/workflows/test.donna.md"
        )
        assert normalize_path("@/workflows", tmp_path).unwrap() == "@/workflows"
        assert normalize_path("@/README", tmp_path).unwrap() == "@/README"

    def test_normalizes_absolute_path_inside_project(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflows" / "test.donna.md"
        project_file.parent.mkdir()
        project_file.write_text("", encoding="utf-8")

        assert normalize_path(str(project_file), tmp_path).unwrap() == "@/workflows/test.donna.md"

    def test_normalizes_relative_path_from_cwd(self, tmp_path: pathlib.Path) -> None:
        cwd = tmp_path / "workflows"
        cwd.mkdir()

        assert normalize_path("test.donna.md", tmp_path, cwd=cwd).unwrap() == "@/workflows/test.donna.md"

    def test_rejects_path_outside_project(self, tmp_path: pathlib.Path) -> None:
        outside = tmp_path.parent / "outside.donna.md"

        assert normalize_path(str(outside), tmp_path).is_err()
        assert normalize_path("../outside.donna.md", tmp_path, cwd=tmp_path).is_err()


class TestNormalizeExistingPath:
    def test_normalizes_existing_file(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflows" / "test.donna.md"
        project_file.parent.mkdir()
        project_file.write_text("", encoding="utf-8")

        assert normalize_existing_path(UntrustedPath(project_file), tmp_path).unwrap() == "@/workflows/test.donna.md"

    def test_rejects_project_root(self, tmp_path: pathlib.Path) -> None:
        assert normalize_existing_path(UntrustedPath(tmp_path), tmp_path).is_err()


class TestNormalizeProjectPath:
    def test_normalizes_parent_relative_to_artifact_file(self, tmp_path: pathlib.Path) -> None:
        relative_to = ArtifactId("@/workflows/rfc/do.donna.md")

        assert (
            normalize_project_path("../plan.donna.md", tmp_path, relative_to=relative_to).unwrap()
            == "@/workflows/plan.donna.md"
        )

    def test_uses_normalize_path_without_artifact_base(self, tmp_path: pathlib.Path) -> None:
        assert normalize_project_path("@/workflow.donna.md", tmp_path).unwrap() == "@/workflow.donna.md"

    def test_rejects_invalid_artifact_path(self, tmp_path: pathlib.Path) -> None:
        assert normalize_project_path(
            "../outside.donna.md", tmp_path, relative_to=ArtifactId("@/file.donna.md")
        ).is_err()

        assert normalize_project_path("", tmp_path).is_err()
        assert normalize_project_path(None, tmp_path).is_err()  # type: ignore[arg-type]

    def test_normalizes_relative_to_artifact_file(self, tmp_path: pathlib.Path) -> None:
        relative_to = ArtifactId("@/workflows/rfc/do.donna.md")

        assert normalize_project_path("specs/design.md", tmp_path, relative_to=relative_to).unwrap() == (
            "@/workflows/rfc/specs/design.md"
        )

    def test_normalizes_absolute_path_when_artifact_base_is_present(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "specs" / "design.md"
        project_file.parent.mkdir()
        project_file.write_text("", encoding="utf-8")
        relative_to = ArtifactId("@/workflows/rfc/do.donna.md")

        assert (
            normalize_project_path(str(project_file), tmp_path, relative_to=relative_to).unwrap()
            == "@/specs/design.md"
        )

    def test_accepts_project_paths_with_non_workflow_extensions(self, tmp_path: pathlib.Path) -> None:
        assert normalize_project_path("@/specs/design.md", tmp_path).unwrap() == "@/specs/design.md"

    def test_accepts_project_paths_without_suffixes(self, tmp_path: pathlib.Path) -> None:
        assert normalize_project_path("@/workflows", tmp_path).unwrap() == "@/workflows"
        assert normalize_project_path("@/README", tmp_path).unwrap() == "@/README"


class TestNormalizeArtifactId:
    def test_propagates_shared_path_error(self, tmp_path: pathlib.Path) -> None:
        result = normalize_artifact_id("@/../workflow.donna.md", tmp_path)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], InvalidProjectPath)

    def test_returns_artifact_id_for_valid_path(self, tmp_path: pathlib.Path) -> None:
        assert normalize_artifact_id("@/workflow.donna.md", tmp_path).unwrap() == ArtifactId("@/workflow.donna.md")

    def test_returns_artifact_id_for_relative_path_from_cwd(self, tmp_path: pathlib.Path) -> None:
        cwd = tmp_path / "workflows"
        cwd.mkdir()

        assert normalize_artifact_id("test.donna.md", tmp_path, cwd=cwd).unwrap() == ArtifactId(
            "@/workflows/test.donna.md"
        )

    def test_rejects_invalid_artifact_id_path(self, tmp_path: pathlib.Path) -> None:
        for value in ("@/workflow", "@/workflow.md"):
            result = normalize_artifact_id(value, tmp_path)

            assert result.is_err()
            assert isinstance(result.unwrap_err()[0], InvalidIdFormat)


class TestNormalizeArtifactSectionId:
    def test_propagates_shared_path_error(self, tmp_path: pathlib.Path) -> None:
        value = "@/../workflow.donna.md"
        result = normalize_artifact_section_id(value + ":step", tmp_path)

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, InvalidProjectPath)
        assert error.path == value

    def test_returns_artifact_section_id_for_valid_input(self, tmp_path: pathlib.Path) -> None:
        assert (
            normalize_artifact_section_id("@/workflow.donna.md:step", tmp_path).unwrap() == "@/workflow.donna.md:step"
        )

    def test_returns_artifact_section_id_relative_to_artifact_file(self, tmp_path: pathlib.Path) -> None:
        relative_to = ArtifactId("@/workflows/rfc/do.donna.md")

        assert (
            normalize_artifact_section_id("../plan.donna.md:step", tmp_path, relative_to=relative_to).unwrap()
            == "@/workflows/plan.donna.md:step"
        )

    @pytest.mark.parametrize("value", ["", "@/workflow.donna.md", "@/workflow.donna.md:---", "@/workflow.md:step"])
    def test_rejects_missing_or_invalid_section(self, tmp_path: pathlib.Path, value: str) -> None:
        result = normalize_artifact_section_id(value, tmp_path)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], InvalidIdFormat)
