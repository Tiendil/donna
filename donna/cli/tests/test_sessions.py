import pathlib

import pytest

from donna.cli.tests import helpers


class TestNewSession:
    @pytest.mark.parametrize("protocol", ["llm", "automation"])
    def test_creates_fresh_session_state(self, tmp_path: pathlib.Path, protocol: str) -> None:
        config_path = helpers.write_config(tmp_path)

        result = helpers.invoke(["--config", str(config_path), "-p", protocol, "new-session"])

        assert result.exit_code == 0
        assert not result.stderr
        if protocol == "automation":
            records = helpers.json_lines(result.stdout)
            success_records = [record for record in records if record.get("type") == "operation_succeeded"]
            assert len(success_records) == 1
            assert success_records[0]["content"] == "Created new session state."
        else:
            assert "kind=operation_succeeded" in result.stdout
            assert "type=operation_succeeded" in result.stdout
        assert (tmp_path / ".session" / "donna" / "state.json").is_file()


class TestStatus:
    def test_reports_new_session_status(self, tmp_path: pathlib.Path) -> None:
        config_path = helpers.write_config(tmp_path)

        result = helpers.invoke(["--config", str(config_path), "-p", "llm", "status"])

        assert result.exit_code == 0
        assert "kind=session_state_status" in result.output
        assert "tasks=0" in result.output
        assert "queued_work_units=0" in result.output
        assert "pending_action_requests=0" in result.output
        assert "This is a new session" in result.output
