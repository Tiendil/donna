import pathlib

import pytest
from pytest_mock import MockerFixture

from donna.cli.tests import helpers


class TestInit:
    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    @pytest.mark.parametrize("content", [None, b"\xff"])
    def test_template_failure__uses_shared_configuration_error(
        self, mocker: MockerFixture, tmp_path: pathlib.Path, protocol: str, content: bytes | None
    ) -> None:
        fixtures = tmp_path / "fixtures"
        fixtures.mkdir()
        if content is not None:
            (fixtures / "base_config.toml").write_bytes(content)
        mocker.patch("llm_tool_cli.config.files.importlib.resources.files", return_value=tmp_path)
        config_path = tmp_path / "donna.toml"

        result = helpers.invoke(["--config", str(config_path), "-p", protocol, "init"])

        assert result.exit_code == 2
        assert not config_path.exists()
        if protocol == "automation":
            assert not result.stderr
            records = helpers.json_lines(result.stdout)
            assert len(records) == 1
            record = records[0]
            assert record["type"] == "error"
            assert record["code"] == "config_template_unreadable"
            assert record["path"] == str(config_path)
            assert record["template"] == "base_config.toml"
            assert record["reason"]
            assert record["content"]
        else:
            assert not result.stdout
            separator = " = " if protocol == "human" else "="
            assert f"kind{separator}error\n" in result.stderr
            assert f"code{separator}config_template_unreadable\n" in result.stderr
            assert f"path{separator}{config_path}\n" in result.stderr
            assert f"template{separator}base_config.toml\n" in result.stderr

    def test_config_home_marker__selects_target_in_home(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        mocker.patch.dict("os.environ", {"HOME": str(tmp_path)})

        result = helpers.invoke(["--config", "~/custom.toml", "-p", "automation", "init"])

        assert result.exit_code == 0
        assert (tmp_path / "custom.toml").is_file()

    def test_existing_config__uses_shared_error_without_overwriting(self, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / "donna.toml"
        config_path.write_text("version = 1", encoding="utf-8")

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", "init"])

        assert result.exit_code == 2
        record = helpers.json_lines(result.stdout)[0]
        assert record["code"] == "config_already_exists"
        assert record["path"] == str(config_path)
        assert not result.stderr
        assert config_path.read_text(encoding="utf-8") == "version = 1"

    def test_missing_parent__uses_shared_error_without_creating_directories(self, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / "missing" / "donna.toml"

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", "init"])

        assert result.exit_code == 2
        record = helpers.json_lines(result.stdout)[0]
        assert record["code"] == "config_unwritable"
        assert record["path"] == str(config_path)
        assert not config_path.parent.exists()

    def test_creates_config_in_current_directory_by_default(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
    ) -> None:
        monkeypatch.chdir(tmp_path)

        result = helpers.invoke(["-p", "automation", "init"])

        assert result.exit_code == 0
        assert (tmp_path / "donna.toml").is_file()
        records = helpers.json_lines(result.output)
        assert records[0]["content"] == "Donna project initialized successfully"
        assert records[0]["type"] == "operation_succeeded"
        assert not result.stderr

    @pytest.mark.parametrize("protocol", ["human", "llm"])
    def test_config_option_selects_target_file(self, tmp_path: pathlib.Path, protocol: str) -> None:
        config_path = tmp_path / "custom.toml"

        result = helpers.invoke(["--config", str(config_path), "-p", protocol, "init"])

        assert result.exit_code == 0
        assert config_path.is_file()
        separator = " = " if protocol == "human" else "="
        assert f"kind{separator}operation_succeeded" in result.stdout
        assert f"type{separator}operation_succeeded" in result.stdout
        assert not result.stderr
