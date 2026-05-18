from donna.cli.tests import helpers


class TestSkill:
    def test_default_document_outputs_usage_skill_without_workspace_config(self) -> None:
        result = helpers.invoke(["-p", "llm", "skill"])

        assert result.exit_code == 0
        assert "kind=skill" in result.output
        assert "document=usage" in result.output
        assert "# `donna` Usage" in result.output

    def test_document_argument_selects_skill_document(self) -> None:
        result = helpers.invoke(["-p", "automation", "skill", "configuration"])

        assert result.exit_code == 0
        records = helpers.json_lines(result.output)
        assert records[0]["document"] == "configuration"
        content = records[0]["content"]
        assert isinstance(content, str)
        assert content.startswith("# `donna` Configuration")

    def test_unknown_document_fails_as_invalid_cli_argument(self) -> None:
        result = helpers.invoke(["skill", "missing"])

        assert result.exit_code != 0
        assert "Invalid value" in result.output
