import pathlib

from donna.domain.artifact_ids import ArtifactId
from donna.domain.paths import ProjectRootPath, ResolvedProjectPath, UntrustedPath
from donna.workspaces import paths
from donna.workspaces.paths import (
    normalize_artifact_id,
    normalize_artifact_path,
    normalize_artifact_section_id,
    normalize_existing_path,
    normalize_path,
    resolve_project_path,
    resolve_project_root,
)


class TestAppendNormalizedPart:
    def test_appends_regular_parts_and_skips_current_dir(self) -> None:
        parts = ["workflows"]

        assert paths._append_normalized_part(parts, ".")
        assert paths._append_normalized_part(parts, "nested")
        assert parts == ["workflows", "nested"]

    def test_rejects_empty_part_and_root_escape(self) -> None:
        assert not paths._append_normalized_part([], "")
        assert not paths._append_normalized_part([], "..")

    def test_parent_part_removes_previous_part(self) -> None:
        parts = ["workflows", "nested"]

        assert paths._append_normalized_part(parts, "..")
        assert parts == ["workflows"]


class TestNormalizeParts:
    def test_returns_canonical_project_path(self) -> None:
        assert paths._normalize_parts("workflows/./nested/../test.donna.md") == "@/workflows/test.donna.md"

    def test_uses_initial_parts_for_relative_artifact_paths(self) -> None:
        assert (
            paths._normalize_parts("../plan.donna.md", initial_parts=("workflows", "rfc"))
            == "@/workflows/plan.donna.md"
        )

    def test_rejects_empty_root_and_invalid_artifact_paths(self) -> None:
        assert paths._normalize_parts("") is None
        assert paths._normalize_parts(".") is None
        assert paths._normalize_parts("invalid name.donna.md") is None


class TestResolveProjectRoot:
    def test_returns_resolved_root_path(self, tmp_path: pathlib.Path) -> None:
        project = tmp_path / "project"
        project.mkdir()
        root = project / ".." / "project"

        assert resolve_project_root(UntrustedPath(root)) == project


class TestNormalizeRootAnchored:
    def test_normalizes_root_anchored_path(self) -> None:
        assert paths._normalize_root_anchored("@/workflows/../plan.donna.md") == "@/plan.donna.md"

    def test_rejects_non_root_anchored_path(self) -> None:
        assert paths._normalize_root_anchored("workflow.donna.md") is None


class TestResolveInsideProject:
    def test_returns_resolved_project_path_inside_root(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflow.donna.md"
        project_file.write_text("", encoding="utf-8")

        assert paths._resolve_inside_project(
            UntrustedPath(project_file),
            ProjectRootPath(tmp_path),
        ) == ResolvedProjectPath(project_file)

    def test_rejects_project_root_and_outside_paths(self, tmp_path: pathlib.Path) -> None:
        assert paths._resolve_inside_project(UntrustedPath(tmp_path), ProjectRootPath(tmp_path)) is None
        assert paths._resolve_inside_project(UntrustedPath(tmp_path.parent), ProjectRootPath(tmp_path)) is None


class TestCanonicalFromResolved:
    def test_returns_canonical_path_for_valid_resolved_path(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflow.donna.md"

        assert (
            paths._canonical_from_resolved(ResolvedProjectPath(project_file), ProjectRootPath(tmp_path))
            == "@/workflow.donna.md"
        )

    def test_rejects_invalid_artifact_path(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "invalid name.donna.md"

        assert paths._canonical_from_resolved(ResolvedProjectPath(project_file), ProjectRootPath(tmp_path)) is None


class TestResolveRootAnchoredPath:
    def test_resolves_root_anchored_path_inside_project(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflow.donna.md"
        project_file.write_text("", encoding="utf-8")

        assert paths._resolve_root_anchored_path("@/workflow.donna.md", ProjectRootPath(tmp_path)) == project_file

    def test_rejects_invalid_root_anchored_path(self, tmp_path: pathlib.Path) -> None:
        assert paths._resolve_root_anchored_path("@/invalid name.donna.md", ProjectRootPath(tmp_path)) is None


class TestResolveProjectPath:
    def test_resolves_root_anchored_path_inside_project(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflows" / "test.donna.md"
        project_file.parent.mkdir()
        project_file.write_text("", encoding="utf-8")

        assert resolve_project_path("@/workflows/test.donna.md", tmp_path) == project_file

    def test_resolves_absolute_path_inside_project(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflows" / "test.donna.md"
        project_file.parent.mkdir()
        project_file.write_text("", encoding="utf-8")

        assert resolve_project_path(str(project_file), tmp_path) == project_file

    def test_rejects_root_escape_and_project_root(self, tmp_path: pathlib.Path) -> None:
        assert resolve_project_path("@/../outside.donna.md", tmp_path) is None
        assert resolve_project_path("@/.", tmp_path) is None

    def test_rejects_absolute_path_when_not_allowed(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflow.donna.md"
        project_file.write_text("", encoding="utf-8")

        assert resolve_project_path(str(project_file), tmp_path, allow_absolute=False) is None


class TestNormalizePath:
    def test_normalizes_root_anchored_path(self, tmp_path: pathlib.Path) -> None:
        assert normalize_path("@/workflows/./nested/../test.donna.md", tmp_path) == "@/workflows/test.donna.md"

    def test_normalizes_absolute_path_inside_project(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflows" / "test.donna.md"
        project_file.parent.mkdir()
        project_file.write_text("", encoding="utf-8")

        assert normalize_path(str(project_file), tmp_path) == "@/workflows/test.donna.md"

    def test_normalizes_relative_path_from_cwd(self, tmp_path: pathlib.Path) -> None:
        cwd = tmp_path / "workflows"
        cwd.mkdir()

        assert normalize_path("test.donna.md", tmp_path, cwd=cwd) == "@/workflows/test.donna.md"

    def test_rejects_path_outside_project(self, tmp_path: pathlib.Path) -> None:
        outside = tmp_path.parent / "outside.donna.md"

        assert normalize_path(str(outside), tmp_path) is None
        assert normalize_path("../outside.donna.md", tmp_path, cwd=tmp_path) is None


class TestNormalizeExistingPath:
    def test_normalizes_existing_file(self, tmp_path: pathlib.Path) -> None:
        project_file = tmp_path / "workflows" / "test.donna.md"
        project_file.parent.mkdir()
        project_file.write_text("", encoding="utf-8")

        assert normalize_existing_path(UntrustedPath(project_file), tmp_path) == "@/workflows/test.donna.md"

    def test_rejects_project_root(self, tmp_path: pathlib.Path) -> None:
        assert normalize_existing_path(UntrustedPath(tmp_path), tmp_path) is None


class TestNormalizeArtifactPath:
    def test_normalizes_relative_to_artifact_file(self, tmp_path: pathlib.Path) -> None:
        relative_to = ArtifactId("@/workflows/rfc/do.donna.md")

        assert (
            normalize_artifact_path("../plan.donna.md", tmp_path, relative_to=relative_to)
            == "@/workflows/plan.donna.md"
        )

    def test_uses_normalize_path_without_artifact_base(self, tmp_path: pathlib.Path) -> None:
        assert normalize_artifact_path("@/workflow.donna.md", tmp_path) == "@/workflow.donna.md"

    def test_rejects_invalid_artifact_path(self, tmp_path: pathlib.Path) -> None:
        assert (
            normalize_artifact_path("../outside.donna.md", tmp_path, relative_to=ArtifactId("@/file.donna.md")) is None
        )

        assert normalize_artifact_path("", tmp_path) is None
        assert normalize_artifact_path(None, tmp_path) is None  # type: ignore[arg-type]


class TestNormalizeFromArtifact:
    def test_normalizes_root_anchored_and_artifact_relative_paths(self) -> None:
        relative_to = ArtifactId("@/workflows/rfc/do.donna.md")

        assert paths._normalize_from_artifact("@/plan.donna.md", relative_to) == "@/plan.donna.md"
        assert paths._normalize_from_artifact("../plan.donna.md", relative_to) == "@/workflows/plan.donna.md"


class TestNormalizeArtifactId:
    def test_returns_artifact_id_for_valid_path(self, tmp_path: pathlib.Path) -> None:
        assert normalize_artifact_id("@/workflow.donna.md", tmp_path) == ArtifactId("@/workflow.donna.md")

    def test_returns_artifact_id_for_relative_path_from_cwd(self, tmp_path: pathlib.Path) -> None:
        cwd = tmp_path / "workflows"
        cwd.mkdir()

        assert normalize_artifact_id("test.donna.md", tmp_path, cwd=cwd) == ArtifactId("@/workflows/test.donna.md")

    def test_rejects_invalid_artifact_id_path(self, tmp_path: pathlib.Path) -> None:
        assert normalize_artifact_id("@/workflow", tmp_path) is None


class TestNormalizeArtifactSectionId:
    def test_returns_artifact_section_id_for_valid_input(self, tmp_path: pathlib.Path) -> None:
        assert normalize_artifact_section_id("@/workflow.donna.md:step", tmp_path) == "@/workflow.donna.md:step"

    def test_returns_artifact_section_id_relative_to_artifact_file(self, tmp_path: pathlib.Path) -> None:
        relative_to = ArtifactId("@/workflows/rfc/do.donna.md")

        assert (
            normalize_artifact_section_id("../plan.donna.md:step", tmp_path, relative_to=relative_to)
            == "@/workflows/plan.donna.md:step"
        )

    def test_rejects_missing_or_invalid_section(self, tmp_path: pathlib.Path) -> None:
        assert normalize_artifact_section_id("@/workflow.donna.md", tmp_path) is None
        assert normalize_artifact_section_id("@/workflow.donna.md:---", tmp_path) is None
