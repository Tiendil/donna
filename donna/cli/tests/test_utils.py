import io
import pathlib
import re
import sys

import pytest
from llm_tool_cli.config import errors as config_errors
from llm_tool_cli.core import errors as llm_tool_errors
from llm_tool_cli.core.result import Err, Ok, UnwrapError
from llm_tool_cli.protocol import Protocol
from llm_tool_cli.protocol.logic_cells import ContentCell
from llm_tool_cli.protocol.output_cells import HumanOutputCell
from llm_tool_cli.protocol.output_cells.base import RenderContext
from pytest_mock import MockerFixture

from donna.cli.tests import helpers
from donna.cli.utils import CliEmitter
from donna.context import Context, context, reset_context, set_context
from donna.domain.artifact_ids import ArtifactId
from donna.machine import context as machine_context
from donna.protocol.tests.make import cell, journal_record
from donna.workspaces import errors as workspace_errors


class TestCliEmitter:
    @pytest.mark.parametrize(
        ("mode", "expected"),
        [
            (Protocol.human, "----- DONNA CELL <cell-id> -----\nkind = sample_status\n\n"),
            (
                Protocol.llm,
                "--DONNA-CELL <cell-id> BEGIN--\nkind=sample_status\n" "--DONNA-CELL <cell-id> END--\n",
            ),
            (Protocol.automation, '{"content":null,"id":"<cell-id>"}\n'),
        ],
    )
    def test_emit_cells__preserves_donna_framing(self, mocker: MockerFixture, mode: Protocol, expected: str) -> None:
        stdout = io.StringIO()
        mocker.patch.object(sys, "stdout", stdout)

        CliEmitter(mode).emit_cells([cell(media_type=None, content=None, meta={})])

        assert re.sub(r"[A-Za-z0-9_-]{22}", "<cell-id>", stdout.getvalue()) == expected

    @pytest.mark.parametrize("mode", list(Protocol))
    def test_emit_cells__supports_text_only_streams(self, mocker: MockerFixture, mode: Protocol) -> None:
        stdout = io.StringIO()
        mocker.patch.object(sys, "stdout", stdout)

        CliEmitter(mode).emit_cells([cell(content="  日本語  ")])

        output = stdout.getvalue()
        assert "日本語" in output
        assert output.endswith("\n\n" if mode == Protocol.human else "\n")
        if mode == Protocol.automation:
            record = helpers.json_lines(output)[0]
            assert record["content"] == "日本語"
            assert re.fullmatch(r"[A-Za-z0-9_-]{22}", str(record["id"]))

    @pytest.mark.parametrize("mode", list(Protocol))
    def test_emit_journal__keeps_consecutive_records_separate(self, mocker: MockerFixture, mode: Protocol) -> None:
        stdout = io.StringIO()
        mocker.patch.object(sys, "stdout", stdout)
        emitter = CliEmitter(mode)

        emitter.emit_journal(journal_record(message="日本語"))
        emitter.emit_journal(journal_record(message="Next step"))

        lines = stdout.getvalue().splitlines()
        assert len(lines) == 2
        assert "日本語" in lines[0]
        assert "Next step" in lines[1]
        assert stdout.getvalue().endswith("\n")

    def test_emit_cells__preserves_batch_context(self, mocker: MockerFixture) -> None:
        stdout = io.StringIO()
        mocker.patch.object(sys, "stdout", stdout)

        def render(cell: HumanOutputCell, context: RenderContext) -> bytes:
            return f"{context.tool_label} {context.index}/{context.total}: {cell.content}\n".encode()

        mocker.patch.object(HumanOutputCell, "render", autospec=True, side_effect=render)
        cells = (ContentCell(kind="item", content=text, media_type="text/markdown") for text in ["first", "second"])

        CliEmitter(Protocol.human).emit_cells(cells)

        assert stdout.getvalue() == "DONNA 0/2: first\nDONNA 1/2: second\n"


class TestCommandContext:
    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    def test_local_errors__use_shared_cells_and_keep_stdout_and_exit_policy(
        self, mocker: MockerFixture, protocol: str
    ) -> None:
        error = workspace_errors.ArtifactNotFound(artifact_id=ArtifactId("@/missing.donna.md"))
        mocker.patch("donna.cli.utils.locate_config", return_value=Err([error]))

        result = helpers.invoke(["-p", protocol, "list"])

        assert result.exit_code == 0
        assert not result.stderr
        if protocol == "automation":
            record = helpers.json_lines(result.stdout)[0]
            assert set(record) == {"id", "type", "code", "artifact_id", "content"}
            assert record["type"] == "error"
            assert record["code"] == error.code
            assert record["artifact_id"] == error.artifact_id
            content = str(record["content"])
        else:
            separator = " = " if protocol == "human" else "="
            assert f"kind{separator}error\n" in result.stdout
            assert f"code{separator}{error.code}\n" in result.stdout
            assert f"artifact_id{separator}{error.artifact_id}\n" in result.stdout
            content = result.stdout
        assert error.format_message() in content
        assert "Ways to fix:" in content
        assert error.ways_to_fix[0].format(error=error) in content
        assert "Error for artifact" not in content

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
        assert set(record) == {"id", "type", "code", "content", "path", "reason"}
        assert record["type"] == "error"
        assert record["code"] == code
        assert record["path"] == str(config_path)
        assert record["reason"]
        assert record["content"] == f"{config_path}: {record['reason']}"

    @pytest.mark.parametrize("protocol", ["human", "llm"])
    def test_shared_config_errors__write_cells_to_stderr(
        self, mocker: MockerFixture, tmp_path: pathlib.Path, protocol: str
    ) -> None:
        failure = config_errors.DiscoveryFailed(path=tmp_path, reason="permission denied")
        mocker.patch("donna.cli.utils.locate_config", return_value=Err([failure]))

        result = helpers.invoke(["-p", protocol, "list"])

        assert result.exit_code == 2
        assert not result.stdout
        assert result.stderr.startswith("----- DONNA CELL " if protocol == "human" else "--DONNA-CELL ")
        assert failure.format_message() in result.stderr
        assert ("kind = error" if protocol == "human" else "kind=error") in result.stderr

    def test_other_shared_errors__preserve_record_and_exit_three(self, mocker: MockerFixture) -> None:
        failure = llm_tool_errors.EnvironmentError(message="service unavailable", code="service_unavailable")
        mocker.patch("donna.cli.utils.locate_config", return_value=Err([failure]))

        result = helpers.invoke(["-p", "automation", "list"])

        assert result.exit_code == 3
        helpers.assert_error_cells(helpers.json_lines(result.stdout), [failure])
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
            helpers.assert_error_cells(helpers.json_lines(result.stdout), [failure])
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
        assert records[0]["code"] == local.code
        assert records[0]["artifact_id"] == local.artifact_id
        helpers.assert_error_cells(records[1:], [config_failure, shared])
        assert not result.stderr

    def test_unrecognized_unwrap_payload__is_not_silently_dropped(self, mocker: MockerFixture) -> None:
        failure = UnwrapError(error=[])
        failure.details["error"] = ["unexpected payload"]
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
        assert record["code"] == "donna.workspaces.config_create_failed"
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
