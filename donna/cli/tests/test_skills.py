import pytest

from donna.cli.tests import helpers
from donna.skills.entities import SkillDocument


class TestSkill:
    @pytest.mark.parametrize("protocol", [None, "human", "llm"])
    def test_default_document_outputs_usage_skill_without_workspace_config(self, protocol: str | None) -> None:
        result = helpers.invoke(["-p", protocol, "skill"] if protocol else ["skill"])

        assert result.exit_code == 0
        assert result.stderr == ""
        separator = "=" if protocol == "llm" else " = "
        assert f"kind{separator}skill\n" in result.output
        assert f"type{separator}skill\n" in result.output
        assert f"document{separator}usage\n" in result.output
        assert "# `donna` Usage" in result.output

    @pytest.mark.parametrize("document", list(SkillDocument))
    def test_document_argument_selects_skill_document(self, document: SkillDocument) -> None:
        result = helpers.invoke(["-p", "automation", "skill", document.value])

        assert result.exit_code == 0
        assert result.stderr == ""
        records = helpers.json_lines(result.output)
        assert len(records) == 1
        assert records[0]["type"] == "skill"
        assert records[0]["document"] == document.value
        content = records[0]["content"]
        assert isinstance(content, str)
        assert content.startswith(f"# `donna` {document.value.title()}")

    def test_unknown_document_fails_as_invalid_cli_argument(self) -> None:
        result = helpers.invoke(["skill", "missing"])

        assert result.exit_code != 0
        assert "Invalid value" in result.output
