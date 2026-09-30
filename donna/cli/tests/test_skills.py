from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from donna.cli.tests import helpers
from donna.skills.entities import SkillDocument


class TestSkill:
    def test_default_protocol_with_explicit_document_and_missing_config(self, tmp_path: Path) -> None:
        result = helpers.invoke(["--config", str(tmp_path / "missing.toml"), "skill", "configuration"])

        assert result.exit_code == 0
        assert not result.stderr
        assert result.stdout.startswith("--DONNA-CELL ")
        assert "document=configuration\n" in result.stdout
        assert "# `donna` Configuration" in result.stdout

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    @pytest.mark.parametrize("content", [None, b"\xff"])
    def test_unreadable_document_reports_shared_error(
        self, tmp_path: Path, mocker: MockerFixture, protocol: str, content: bytes | None
    ) -> None:
        fixtures = tmp_path / "fixtures"
        fixtures.mkdir()
        if content is not None:
            (fixtures / "usage.md").write_bytes(content)
        mocker.patch("llm_tool_cli.skills.fixtures.importlib.resources.files", return_value=tmp_path)

        result = helpers.invoke(["-p", protocol, "skill"])

        assert result.exit_code == 3
        if protocol == "automation":
            records = helpers.json_lines(result.stdout)
            assert len(records) == 1
            assert records[0]["type"] == "error"
            assert records[0]["code"] == "skill_unreadable"
            assert records[0]["document"] == "usage"
            assert records[0]["reason"]
            assert records[0]["content"]
            assert result.stderr == ""
        else:
            assert result.stdout == ""
            separator = "=" if protocol == "llm" else " = "
            assert f"kind{separator}error\n" in result.stderr
            assert f"code{separator}skill_unreadable\n" in result.stderr
            assert f"document{separator}usage\n" in result.stderr

    @pytest.mark.parametrize("protocol", [None, "human", "llm"])
    def test_default_document_outputs_usage_skill_without_workspace_config(self, protocol: str | None) -> None:
        result = helpers.invoke(["-p", protocol, "skill"] if protocol else ["skill"])

        assert result.exit_code == 0
        assert result.stderr == ""
        separator = " = " if protocol == "human" else "="
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
