import importlib.resources

from donna.skills import SkillDocument


def test_fixture_resources__match_public_document_names() -> None:
    fixture_dir = importlib.resources.files("donna.skills").joinpath("fixtures")

    fixture_names = sorted(resource.name for resource in fixture_dir.iterdir() if resource.name.endswith(".md"))

    assert fixture_names == sorted(f"{document.value}.md" for document in SkillDocument)
