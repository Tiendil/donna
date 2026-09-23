import pathlib

import pytest
from pytest_mock import MockerFixture

from donna.cli.tests import helpers


class TestInit:
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

    def test_config_option_selects_target_file(self, tmp_path: pathlib.Path) -> None:
        config_path = tmp_path / "custom.toml"

        result = helpers.invoke(["--config", str(config_path), "-p", "llm", "init"])

        assert result.exit_code == 0
        assert config_path.is_file()
        assert "kind=operation_succeeded" in result.output
