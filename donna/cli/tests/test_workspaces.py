import pathlib

import pytest

from donna.cli.tests import helpers


class TestInit:
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
