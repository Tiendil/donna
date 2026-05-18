import importlib.resources

import pytest

from donna.skills import SkillDocument, load_skill_text

EXPECTED_DOCUMENT_HEADINGS = {
    SkillDocument.usage: "# `donna` Usage",
    SkillDocument.configuration: "# `donna` Configuration",
    SkillDocument.initialization: "# `donna` Initialization",
    SkillDocument.workflows: "# `donna` Workflows",
}


class TestLoadSkillText:
    def test_default_document_is_usage(self) -> None:
        assert load_skill_text() == load_skill_text(SkillDocument.usage)

    @pytest.mark.parametrize(("document", "heading"), EXPECTED_DOCUMENT_HEADINGS.items())
    def test_loads_document_text(self, document: SkillDocument, heading: str) -> None:
        assert load_skill_text(document).startswith(f"{heading}\n")


def test_fixture_resources__match_public_document_names() -> None:
    fixture_dir = importlib.resources.files("donna.skills").joinpath("fixtures")

    fixture_names = sorted(resource.name for resource in fixture_dir.iterdir() if resource.name.endswith(".md"))

    assert fixture_names == sorted(f"{document.value}.md" for document in SkillDocument)
