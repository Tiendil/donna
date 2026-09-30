import pathlib
import re
from importlib import metadata

import pytest

from donna.cli.tests import helpers


class TestVersion:
    @pytest.mark.parametrize("protocol", [None, "human", "llm", "automation"])
    def test_prints_version_cell_without_workspace(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, protocol: str | None
    ) -> None:
        monkeypatch.chdir(tmp_path)
        version = metadata.version("donna")

        options = [] if protocol is None else ["-p", protocol]
        result = helpers.invoke([*options, "version"])

        assert result.exit_code == 0
        assert not result.stderr
        assert not (tmp_path / ".session").exists()
        if protocol == "automation":
            records = helpers.json_lines(result.stdout)
            assert len(records) == 1
            assert records[0].pop("id")
            assert records == [{"type": "version", "version": version, "content": None}]
            assert len(result.stdout.splitlines()) == 1
        else:
            output = re.sub(r"[A-Za-z0-9_-]{22}", "<id>", result.stdout)
            if protocol == "llm":
                assert output == (
                    f"--DONNA-CELL <id> BEGIN--\nkind=version\ntype=version\nversion={version}\n"
                    "--DONNA-CELL <id> END--\n"
                )
            else:
                assert (
                    output == f"----- DONNA CELL <id> -----\nkind = version\ntype = version\nversion = {version}\n\n"
                )

    @pytest.mark.parametrize("content", [None, "not valid TOML"])
    def test_ignores_missing_or_invalid_config(self, tmp_path: pathlib.Path, content: str | None) -> None:
        config_path = tmp_path / "donna.toml"
        if content is not None:
            config_path.write_text(content, encoding="utf-8")

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", "version"])

        assert result.exit_code == 0
        assert not result.stderr
        assert helpers.json_lines(result.stdout)[0]["version"] == metadata.version("donna")
        assert not (tmp_path / ".session").exists()
