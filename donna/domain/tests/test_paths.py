import pytest

from donna.domain.paths import ProjectPathRaw, raw_project_path, validate_project_path_id


class TestRawProjectPath:
    def test_returns_raw_path_without_project_root_prefix(self) -> None:
        assert raw_project_path("@/workflows/test.donna.md") == ProjectPathRaw("workflows/test.donna.md")

    @pytest.mark.parametrize("value", ["@", "@/", "workflows/test.donna.md", None])
    def test_rejects_non_root_anchored_project_paths(self, value: object) -> None:
        assert raw_project_path(value) is None


class TestValidateProjectPathId:
    @pytest.mark.parametrize(
        "value",
        [
            "@/README.md",
            "@/README",
            "@/LICENSE",
            "@/Makefile",
            "@/workflows",
            "@/workflows/polish.donna.md",
            "@/workflows/archive",
            "@/src/donna",
            "@/workflows/Проектный план",
            "@/workflows/project plan.donna.md",
        ],
    )
    def test_accepts_canonical_project_paths(self, value: str) -> None:
        assert validate_project_path_id(value)

    @pytest.mark.parametrize(
        "value",
        [
            "@",
            "@/",
            "@/workflows/../README.md",
            "@/workflows//polish.donna.md",
            "@/workflows/",
            "/home/user/project/workflows/polish.donna.md",
            None,
        ],
    )
    def test_rejects_malformed_project_paths(self, value: object) -> None:
        assert not validate_project_path_id(value)
