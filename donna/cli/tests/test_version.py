import pathlib
import re

import pytest
from pytest_mock import MockerFixture

from donna.cli.tests import helpers


class TestVersion:
    @pytest.mark.parametrize("protocol", [None, "human", "llm", "automation"])
    def test_prints_version_cell_without_workspace(
        self, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, protocol: str | None
    ) -> None:
        monkeypatch.chdir(tmp_path)
        helpers.load_cli_commands()
        mocker.patch("donna.cli.commands.version.importlib.metadata.version", return_value="9.8.7")

        options = [] if protocol is None else ["-p", protocol]
        result = helpers.invoke([*options, "version"])

        assert result.exit_code == 0
        assert not result.stderr
        assert not (tmp_path / ".session").exists()
        if protocol == "automation":
            records = helpers.json_lines(result.stdout)
            assert len(records) == 1
            assert records[0].pop("id")
            assert records == [{"type": "version", "version": "9.8.7", "content": None}]
            assert len(result.stdout.splitlines()) == 1
        else:
            output = re.sub(r"[A-Za-z0-9_-]{22}", "<id>", result.stdout)
            if protocol == "llm":
                assert output == (
                    "--DONNA-CELL <id> BEGIN--\nkind=version\ntype=version\nversion=9.8.7\n"
                    "--DONNA-CELL <id> END--\n"
                )
            else:
                assert output == "----- DONNA CELL <id> -----\nkind = version\ntype = version\nversion = 9.8.7\n\n"

    @pytest.mark.parametrize("content", [None, "not valid TOML"])
    def test_ignores_missing_or_invalid_config(
        self, mocker: MockerFixture, tmp_path: pathlib.Path, content: str | None
    ) -> None:
        config_path = tmp_path / "donna.toml"
        if content is not None:
            config_path.write_text(content, encoding="utf-8")
        helpers.load_cli_commands()
        mocker.patch("donna.cli.commands.version.importlib.metadata.version", return_value="9.8.7")

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", "version"])

        assert result.exit_code == 0
        assert not result.stderr
        assert helpers.json_lines(result.stdout)[0]["version"] == "9.8.7"
        assert not (tmp_path / ".session").exists()

    def test_metadata_failure_propagates(self, mocker: MockerFixture) -> None:
        helpers.load_cli_commands()
        mocker.patch(
            "donna.cli.commands.version.importlib.metadata.version", side_effect=RuntimeError("lookup failed")
        )

        result = helpers.invoke(["-p", "automation", "version"])

        assert isinstance(result.exception, RuntimeError)
        assert not result.stdout
        assert not result.stderr
