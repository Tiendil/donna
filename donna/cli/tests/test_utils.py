import pathlib

import pytest
from llm_tool_cli.config import errors as config_errors
from llm_tool_cli.core.errors import Error as SharedError
from pytest_mock import MockerFixture

from donna.cli.tests import helpers
from donna.context import Context, context, reset_context, set_context
from donna.machine import context as machine_context


class TestCommandContext:
    @pytest.mark.parametrize(
        ("content", "code"),
        [
            (b"version = ", "config_invalid_toml"),
            (b"\xff", "config_invalid_encoding"),
            (b"version = 2", "config_validation_failed"),
            (None, "config_unreadable"),
        ],
    )
    def test_shared_config_errors__emit_shared_automation_records(
        self, tmp_path: pathlib.Path, content: bytes | None, code: str
    ) -> None:
        config_path = tmp_path / "donna.toml"
        if content is not None:
            config_path.write_bytes(content)

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", "list"])

        assert result.exit_code == 2
        assert not result.stderr
        records = helpers.json_lines(result.stdout)
        assert len(records) == 1
        record = records[0]
        assert set(record) == {"type", "code", "message", "path", "reason"}
        assert record["type"] == "error"
        assert record["code"] == code
        assert record["path"] == str(config_path)
        assert record["reason"]
        assert record["message"] == f"{config_path}: {record['reason']}"

    @pytest.mark.parametrize("protocol", ["human", "llm"])
    def test_shared_config_errors__write_text_to_stderr(
        self, mocker: MockerFixture, tmp_path: pathlib.Path, protocol: str
    ) -> None:
        failure = config_errors.DiscoveryFailed(tmp_path, "permission denied")
        mocker.patch("donna.cli.utils.locate_config", side_effect=failure)

        result = helpers.invoke(["-p", protocol, "list"])

        assert result.exit_code == 2
        assert not result.stdout
        assert result.stderr == f"{failure.message}\n"

    def test_other_shared_errors__preserve_record_and_exit_three(self, mocker: MockerFixture) -> None:
        failure = SharedError("service unavailable", code="service_unavailable", details={"attempts": 2})
        mocker.patch("donna.cli.utils.locate_config", side_effect=failure)

        result = helpers.invoke(["-p", "automation", "list"])

        assert result.exit_code == 3
        assert helpers.json_lines(result.stdout) == [failure.as_record()]
        assert not result.stderr

    def test_shared_errors_during_command__restore_runtime_context(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        config_path = helpers.write_config(tmp_path)
        failure = SharedError("command failed", code="command_failed")
        mocker.patch("donna.cli.commands.artifacts._log_artifact_operation", side_effect=failure)
        previous_context = Context()
        context_token = set_context(previous_context)
        machine_context_token = machine_context.set_context(previous_context)
        try:
            result = helpers.invoke(["--config", str(config_path), "-p", "automation", "list"])

            assert result.exit_code == 3
            assert helpers.json_lines(result.stdout) == [failure.as_record()]
            assert context() == previous_context
            assert machine_context.context() == previous_context
        finally:
            machine_context.reset_context(machine_context_token)
            reset_context(context_token)

    def test_unexpected_errors__propagate_without_expected_diagnostic(self, mocker: MockerFixture) -> None:
        failure = RuntimeError("unexpected defect")
        mocker.patch("donna.cli.utils.locate_config", side_effect=failure)

        result = helpers.invoke(["-p", "automation", "list"])

        assert result.exception == failure
        assert not result.stdout
        assert not result.stderr

    def test_local_errors__retain_donna_result_and_cell_behavior(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        mocker.patch(
            "donna.workspaces.initialization.importlib.resources.files", side_effect=OSError("missing template")
        )

        result = helpers.invoke(["--config", str(tmp_path / "donna.toml"), "-p", "automation", "init"])

        assert result.exit_code == 0
        record = helpers.json_lines(result.stdout)[0]
        assert record["error_code"] == "donna.workspaces.config_create_failed"
        assert "content" in record
        assert "id" in record

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    def test_missing_discovered_config__uses_shared_diagnostic(
        self, mocker: MockerFixture, tmp_path: pathlib.Path, protocol: str
    ) -> None:
        mocker.patch("llm_tool_cli.config.files.find_config", return_value=None)
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)

        result = helpers.invoke(["-p", protocol, "list"])

        assert result.exit_code == 2
        if protocol == "automation":
            record = helpers.json_lines(result.stdout)[0]
            assert record["type"] == "error"
            assert record["code"] == "config_not_found"
            assert record["path"] == str(tmp_path)
            assert "donna.toml" in str(record["reason"])
            assert "error_code" not in record
            assert not result.stderr
        else:
            assert not result.stdout
            assert "donna.toml" in result.stderr
            assert str(tmp_path) in result.stderr
