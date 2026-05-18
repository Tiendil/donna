from typing import Any, cast

import pytest

from donna.domain import errors
from donna.domain.artifact_ids import (
    ArtifactId,
    ArtifactSectionId,
    artifact_path_parts,
    artifact_section_id,
    split_artifact_section_id,
    validate_artifact_id,
    validate_artifact_section_id,
)
from donna.domain.ids import SectionId


class TestValidateArtifactId:
    @pytest.mark.parametrize(
        "value",
        [
            "@/README.md",
            "@/workflows/polish.donna.md",
            "@/.session/donna/plans/feature.donna.md",
        ],
    )
    def test_valid_canonical_artifact_id(self, value: str) -> None:
        assert validate_artifact_id(value)

    @pytest.mark.parametrize(
        "value",
        [
            "@",
            "@/",
            "@/workflows/../README.md",
            "@/workflows//polish.donna.md",
            "@/workflows/",
            "@/---/polish.donna.md",
            "@/README",
            "/home/user/project/workflows/polish.donna.md",
            None,
        ],
    )
    def test_invalid_canonical_artifact_id(self, value: object) -> None:
        assert not validate_artifact_id(cast(Any, value))


class TestValidateArtifactSectionId:
    def test_valid_section_id(self) -> None:
        assert validate_artifact_section_id("@/workflows/polish.donna.md:section-1")

    @pytest.mark.parametrize(
        "value",
        [
            "@/workflows/polish.donna.md",
            "@/workflows/polish.donna.md:",
            "@/workflows/polish.donna.md:---",
            "@/workflows//polish.donna.md:section",
            None,
        ],
    )
    def test_invalid_section_id(self, value: object) -> None:
        assert not validate_artifact_section_id(cast(Any, value))


class TestArtifactPathParts:
    def test_valid_artifact_id(self) -> None:
        assert artifact_path_parts(ArtifactId("@/workflows/polish.donna.md")) == ("workflows", "polish.donna.md")

    def test_invalid_artifact_id(self) -> None:
        with pytest.raises(ValueError):
            artifact_path_parts(ArtifactId("workflows/polish.donna.md"))


class TestArtifactSectionId:
    def test_builds_full_section_id(self) -> None:
        full_id = artifact_section_id(ArtifactId("@/workflows/polish.donna.md"), SectionId("start"))

        assert full_id == ArtifactSectionId("@/workflows/polish.donna.md:start")

    def test_builds_from_string_section_id(self) -> None:
        full_id = artifact_section_id(ArtifactId("@/workflows/polish.donna.md"), "finish")

        assert full_id == ArtifactSectionId("@/workflows/polish.donna.md:finish")

    def test_invalid_artifact_id(self) -> None:
        with pytest.raises(ValueError):
            artifact_section_id(ArtifactId("workflows/polish.donna.md"), "start")

    def test_invalid_local_section_id(self) -> None:
        with pytest.raises(errors.InvalidIdentifier):
            artifact_section_id(ArtifactId("@/workflows/polish.donna.md"), "///")


class TestSplitArtifactSectionId:
    def test_valid_section_id(self) -> None:
        parts = split_artifact_section_id("@/workflows/polish.donna.md:section-1")

        assert parts is not None
        assert parts.full_id == ArtifactSectionId("@/workflows/polish.donna.md:section-1")
        assert parts.artifact_id == ArtifactId("@/workflows/polish.donna.md")
        assert parts.section_id == SectionId("section-1")

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "@/workflows/polish.donna.md",
            "@/workflows/polish.donna.md:",
            "@/workflows/polish.donna.md:---",
            "@/workflows//polish.donna.md:section",
            1,
        ],
    )
    def test_invalid_section_id(self, value: object) -> None:
        assert split_artifact_section_id(cast(Any, value)) is None
