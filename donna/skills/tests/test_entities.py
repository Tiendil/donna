from donna.skills import SkillDocument


class TestSkillDocument:
    def test_values__match_public_document_names(self) -> None:
        assert [document.value for document in SkillDocument] == [
            "usage",
            "configuration",
            "initialization",
            "workflows",
        ]
