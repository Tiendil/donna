import pytest

from donna.domain.paths import ProjectPathRaw, raw_project_path


class TestRawProjectPath:
    def test_returns_raw_path_without_project_root_prefix(self) -> None:
        assert raw_project_path("@/workflows/test.donna.md") == ProjectPathRaw("workflows/test.donna.md")

    @pytest.mark.parametrize("value", ["@", "@/", "workflows/test.donna.md", None])
    def test_rejects_non_root_anchored_project_paths(self, value: object) -> None:
        assert raw_project_path(value) is None
