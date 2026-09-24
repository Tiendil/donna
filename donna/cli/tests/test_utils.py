import pathlib

import pytest
from llm_tool_cli.config import errors as config_errors
from llm_tool_cli.core import errors as llm_tool_errors
from llm_tool_cli.core.result import Err, Ok, UnwrapError
from pytest_mock import MockerFixture

from donna.cli.tests import helpers
from donna.context import Context, context, reset_context, set_context
from donna.domain.artifact_ids import ArtifactId
from donna.machine import context as machine_context
from donna.workspaces import errors as workspace_errors


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
        failure = config_errors.DiscoveryFailed(path=tmp_path, reason="permission denied")
        mocker.patch("donna.cli.utils.locate_config", return_value=Err([failure]))

        result = helpers.invoke(["-p", protocol, "list"])

        assert result.exit_code == 2
        assert not result.stdout
        assert result.stderr == f"{failure.format_message()}\n"

    def test_other_shared_errors__preserve_record_and_exit_three(self, mocker: MockerFixture) -> None:
        failure = llm_tool_errors.EnvironmentError(message="service unavailable", code="service_unavailable")
        mocker.patch("donna.cli.utils.locate_config", return_value=Err([failure]))

        result = helpers.invoke(["-p", "automation", "list"])

        assert result.exit_code == 3
        assert helpers.json_lines(result.stdout) == [failure.as_record()]
        assert not result.stderr

    def test_shared_errors_during_command__restore_runtime_context(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        config_path = helpers.write_config(tmp_path)
        failure = llm_tool_errors.EnvironmentError(message="command failed", code="command_failed")
        mocker.patch("donna.cli.commands.artifacts._log_artifact_operation", side_effect=UnwrapError(error=[failure]))
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

    def test_shared_internal_errors__propagate_without_expected_diagnostic(self, mocker: MockerFixture) -> None:
        failure = llm_tool_errors.InternalError("unexpected defect")
        mocker.patch("donna.cli.utils.locate_config", side_effect=failure)

        result = helpers.invoke(["-p", "automation", "list"])

        assert result.exception == failure
        assert not result.stdout
        assert not result.stderr

    def test_mixed_errors__preserves_all_diagnostics(self, mocker: MockerFixture, tmp_path: pathlib.Path) -> None:
        local = workspace_errors.ArtifactNotFound(artifact_id=ArtifactId("@/missing.donna.md"))
        config_failure = config_errors.Unreadable(path=tmp_path / "donna.toml", reason="denied")
        shared = llm_tool_errors.EnvironmentError(code="unavailable", message="Service unavailable")
        mocker.patch("donna.cli.utils.locate_config", return_value=Err([local, config_failure, shared]))

        result = helpers.invoke(["-p", "automation", "list"])

        assert result.exit_code == 3
        records = helpers.json_lines(result.stdout)
        assert records[0]["error_code"] == local.code
        assert records[0]["artifact_id"] == local.artifact_id
        assert records[1:] == [config_failure.as_record(), shared.as_record()]
        assert not result.stderr

    def test_unrecognized_unwrap_payload__is_not_silently_dropped(self, mocker: MockerFixture) -> None:
        failure = UnwrapError(error=["unexpected payload"])
        mocker.patch("donna.cli.utils.locate_config", side_effect=failure)

        result = helpers.invoke(["-p", "automation", "list"])

        assert isinstance(result.exception, UnwrapError)
        assert result.exception.details == failure.details
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
        mocker.patch("llm_tool_cli.config.files.find_config", return_value=Ok(None))
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
