import pathlib

import pytest
from llm_tool_cli.config.project import project_config
from pytest_mock import MockerFixture

from donna.cli.tests import helpers


class TestInit:
    @pytest.mark.parametrize("explicit", [False, True])
    @pytest.mark.parametrize("command", ["init", "list"])
    def test_config_symlink__uses_shared_path_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, explicit: bool, command: str
    ) -> None:
        target = tmp_path / "target.toml"
        target.write_text("version = 1", encoding="utf-8")
        config_path = tmp_path / "donna.toml"
        config_path.symlink_to(target)
        monkeypatch.chdir(tmp_path)
        arguments = ["--config", str(config_path)] if explicit else []

        result = helpers.invoke([*arguments, "-p", "automation", command])

        assert result.exit_code == 3
        record = helpers.json_lines(result.stdout)[0]
        assert record["code"] == "invalid_project_path"
        assert record["path"] == str(config_path)
        assert not result.stderr
        assert not project_config.is_set()
        assert config_path.is_symlink()
        assert target.read_text(encoding="utf-8") == "version = 1"

    @pytest.mark.parametrize(
        "text, code",
        [("version =", "config_invalid_toml"), ('session_dir = "../outside"', "config_validation_failed")],
    )
    def test_invalid_starter__is_not_published_as_a_project(
        self, mocker: MockerFixture, tmp_path: pathlib.Path, text: str, code: str
    ) -> None:
        fixtures = tmp_path / "fixtures"
        fixtures.mkdir()
        (fixtures / "base_config.toml").write_text(text, encoding="utf-8")
        mocker.patch("llm_tool_cli.config.files.importlib.resources.files", return_value=tmp_path)
        path = tmp_path / "donna.toml"

        result = helpers.invoke(["--config", str(path), "-p", "automation", "init"])

        assert result.exit_code == 2
        assert [record["code"] for record in helpers.json_lines(result.stdout)] == [code]
        assert path.read_text(encoding="utf-8") == text
        assert not project_config.is_set()

    def test_parent_config__creates_in_current_directory(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
    ) -> None:
        parent_config = tmp_path / "donna.toml"
        parent_config.write_text("version = 2", encoding="utf-8")
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.chdir(project)

        result = helpers.invoke(["-p", "automation", "init"])

        assert result.exit_code == 0
        assert (project / "donna.toml").is_file()
        assert parent_config.read_text(encoding="utf-8") == "version = 2"
        assert helpers.json_lines(result.stdout)[0]["type"] == "operation_succeeded"
        assert helpers.json_lines(result.stdout)[0]["path"] == str(project / "donna.toml")
        assert not result.stderr

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
            assert not result.stderr
            separator = " = " if protocol == "human" else "="
            assert f"kind{separator}error\n" in result.stdout
            assert f"code{separator}config_template_unreadable\n" in result.stdout
            assert f"path{separator}{config_path}\n" in result.stdout
            assert f"template{separator}base_config.toml\n" in result.stdout

    def test_config_home_marker__selects_target_in_home(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        mocker.patch.dict("os.environ", {"HOME": str(tmp_path)})

        result = helpers.invoke(["--config", "~/custom.toml", "-p", "automation", "init"])

        assert result.exit_code == 0
        assert (tmp_path / "custom.toml").is_file()
        assert helpers.json_lines(result.stdout)[0]["path"] == str(tmp_path / "custom.toml")

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
        text = (tmp_path / "donna.toml").read_text(encoding="utf-8")
        assert 'session_dir = ".session/donna"' in text
        assert '"./workflows"' in text
        assert '"./.session/donna"' in text
        assert "# [defaults]" in text
        assert "# [journal]" in text
        records = helpers.json_lines(result.output)
        assert len(records) == 1
        assert records[0]["content"] == "Configuration created."
        assert records[0]["type"] == "operation_succeeded"
        assert records[0]["path"] == str(tmp_path / "donna.toml")
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
        assert f"path{separator}{config_path}\n" in result.stdout
        assert "Configuration created.\n" in result.stdout
        assert not result.stderr
