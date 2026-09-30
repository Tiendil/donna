import io
import pathlib
import re
import sys

import pytest
from llm_tool_cli.cli.errors import InvalidArguments
from llm_tool_cli.config import errors as config_errors
from llm_tool_cli.core import errors as llm_tool_errors
from llm_tool_cli.core.result import Err, Ok, UnwrapError
from llm_tool_cli.protocol import Protocol
from llm_tool_cli.protocol.logic_cells import ContentCell
from llm_tool_cli.protocol.output_cells import HumanOutputCell
from llm_tool_cli.protocol.output_cells.base import RenderContext
from llm_tool_cli.protocol.tests.helpers import assert_error_cells
from pytest_mock import MockerFixture

from donna.cli.tests import helpers
from donna.cli.utils import CliEmitter
from donna.context import Context, context, reset_context, set_context
from donna.domain.artifact_ids import ArtifactId
from donna.domain.ids import SectionId
from donna.machine import context as machine_context
from donna.primitives.sections.run_script import RunScriptInvalidExitCode
from donna.protocol.tests.make import cell, journal_record
from donna.workspaces import errors as workspace_errors
from donna.workspaces import journal as workspace_journal


class TestCliEmitter:
    @pytest.mark.parametrize("stderr", [False, True])
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
    def test_emit_cells__preserves_donna_framing(
        self, mocker: MockerFixture, mode: Protocol, expected: str, stderr: bool
    ) -> None:
        stdout = io.StringIO()
        error_stream = io.StringIO()
        mocker.patch.object(sys, "stdout", stdout)
        mocker.patch.object(sys, "stderr", error_stream)

        CliEmitter(mode).emit_cells([cell(media_type=None, content=None, meta={})], stderr=stderr)

        output = error_stream.getvalue() if stderr else stdout.getvalue()
        assert re.sub(r"[A-Za-z0-9_-]{22}", "<cell-id>", output) == expected
        assert (stdout.getvalue() if stderr else error_stream.getvalue()) == ""

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
    @pytest.mark.parametrize("command, code", [("list", "config_unreadable"), ("init", "config_already_exists")])
    def test_config_path__directory_is_checked_by_configuration_operation(
        self, tmp_path: pathlib.Path, protocol: str, command: str, code: str
    ) -> None:
        result = helpers.invoke(["--config", str(tmp_path), "-p", protocol, command])

        assert result.exit_code == 2
        assert tmp_path.is_dir()
        assert not list(tmp_path.iterdir())
        if protocol == "automation":
            assert not result.stderr
            records = helpers.json_lines(result.stdout)
            assert len(records) == 1
            assert records[0]["type"] == "error"
            assert records[0]["code"] == code
            assert records[0]["path"] == str(tmp_path)
        else:
            assert not result.stdout
            separator = " = " if protocol == "human" else "="
            assert f"kind{separator}error\n" in result.stderr
            assert f"code{separator}{code}\n" in result.stderr
            assert f"path{separator}{tmp_path}\n" in result.stderr

    @pytest.mark.parametrize("command", ["skill", "version"])
    def test_config_path__unused_directory_does_not_prevent_execution(
        self, tmp_path: pathlib.Path, command: str
    ) -> None:
        result = helpers.invoke(["--config", str(tmp_path), "-p", "automation", command])

        assert result.exit_code == 0
        assert not result.stderr
        records = helpers.json_lines(result.stdout)
        assert len(records) == 1
        assert records[0]["type"] == command
        assert not list(tmp_path.iterdir())

    def test_config_path__does_not_leak_between_invocations(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        helpers.write_config(tmp_path)
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)

        for name in ["first.toml", "second.toml"]:
            result = helpers.invoke(["--config", name, "-p", "automation", "list"])

            assert result.exit_code == 2
            assert not result.stderr
            record = helpers.json_lines(result.stdout)[0]
            assert record["code"] == "config_unreadable"
            assert record["path"] == str(tmp_path / name)

        result = helpers.invoke(["list"])

        assert result.exit_code == 0
        assert not result.stderr
        assert "config_unreadable" not in result.stdout

    def test_protocol_defaults__are_selected_for_each_invocation(self) -> None:
        invocations = [
            (["skill"], "--DONNA-CELL ", "kind=skill\n"),
            (["version"], "----- DONNA CELL ", "kind = version\n"),
            (["-p", "human", "skill"], "----- DONNA CELL ", "kind = skill\n"),
            (["skill"], "--DONNA-CELL ", "kind=skill\n"),
        ]
        for arguments, prefix, kind in invocations:
            result = helpers.invoke(arguments)

            assert result.exit_code == 0
            assert not result.stderr
            assert result.stdout.startswith(prefix)
            assert kind in result.stdout

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    def test_local_errors__use_shared_cells_and_exit_code(self, mocker: MockerFixture, protocol: str) -> None:
        error = workspace_errors.ArtifactNotFound(artifact_id=ArtifactId("@/missing.donna.md"))
        mocker.patch("donna.cli.utils.locate_config", return_value=Err([error]))

        result = helpers.invoke(["-p", protocol, "list"])

        assert result.exit_code == 3
        if protocol == "automation":
            assert not result.stderr
            record = helpers.json_lines(result.stdout)[0]
            assert set(record) == {"id", "type", "code", "artifact_id", "content"}
            assert record["type"] == "error"
            assert record["code"] == error.code
            assert record["artifact_id"] == error.artifact_id
            content = str(record["content"])
        else:
            assert not result.stdout
            separator = " = " if protocol == "human" else "="
            assert f"kind{separator}error\n" in result.stderr
            assert f"code{separator}{error.code}\n" in result.stderr
            assert f"artifact_id{separator}{error.artifact_id}\n" in result.stderr
            content = result.stderr
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
        assert_error_cells(helpers.json_lines(result.stdout), [failure])
        assert not result.stderr

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    def test_invalid_arguments__use_declared_exit_code(self, mocker: MockerFixture, protocol: str) -> None:
        failure = InvalidArguments(reason="invalid argument")
        mocker.patch("donna.cli.utils.locate_config", return_value=Err([failure]))

        result = helpers.invoke(["-p", protocol, "list"])

        assert result.exit_code == 1
        if protocol == "automation":
            assert_error_cells(helpers.json_lines(result.stdout), [failure])
            assert not result.stderr
        else:
            assert not result.stdout
            separator = " = " if protocol == "human" else "="
            assert f"code{separator}invalid_arguments\n" in result.stderr

    def test_shared_errors_during_command__restore_runtime_context(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        config_path = helpers.write_config(tmp_path)
        initialized = helpers.invoke(["--config", str(config_path), "-p", "automation", "new-session"])
        assert initialized.exit_code == 0
        failure = llm_tool_errors.EnvironmentError(message="command failed", code="command_failed")
        mocker.patch("donna.cli.commands.artifacts._log_artifact_operation", side_effect=UnwrapError(error=[failure]))
        journal = mocker.spy(workspace_journal, "write_record")
        previous_context = Context()
        context_token = set_context(previous_context)
        machine_context_token = machine_context.set_context(previous_context)
        try:
            result = helpers.invoke(["--config", str(config_path), "-p", "automation", "list"])

            assert result.exit_code == 3
            records = helpers.json_lines(result.stdout)
            assert_error_cells([record for record in records if record.get("type") == "error"], [failure])
            journal.assert_called_once()
            journal_entry = journal.call_args.args[0]
            assert journal_entry.actor_id == "donna"
            assert failure.code in journal_entry.message
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

    @pytest.mark.parametrize("reverse", [False, True])
    @pytest.mark.parametrize("include_general", [False, True])
    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    def test_mixed_errors__preserves_all_diagnostics_and_uses_highest_code(
        self, mocker: MockerFixture, tmp_path: pathlib.Path, reverse: bool, include_general: bool, protocol: str
    ) -> None:
        local = workspace_errors.ArtifactNotFound(artifact_id=ArtifactId("@/missing.donna.md"))
        config_failure = config_errors.Unreadable(path=tmp_path / "donna.toml", reason="denied")
        failures: llm_tool_errors.EnvironmentErrors = [local, InvalidArguments(reason="invalid"), config_failure]
        if include_general:
            failures.append(llm_tool_errors.EnvironmentError(code="unavailable", message="Service unavailable"))
        if reverse:
            failures.reverse()
        mocker.patch("donna.cli.utils.locate_config", return_value=Err(failures))

        result = helpers.invoke(["-p", protocol, "list"])

        assert result.exit_code == 3
        if protocol == "automation":
            records = helpers.json_lines(result.stdout)
            assert [record["code"] for record in records] == [error.code for error in failures]
            assert records[failures.index(local)]["artifact_id"] == local.artifact_id
            assert all("cli_exit_code" not in record for record in records)
            assert not result.stderr
        else:
            assert not result.stdout
            separator = " = " if protocol == "human" else "="
            codes = [f"code{separator}{error.code}\n" for error in failures]
            assert all(code in result.stderr for code in codes)
            positions = [result.stderr.index(code) for code in codes]
            assert positions == sorted(positions)

    def test_script_exit_code_context__does_not_override_cli_exit_code(self, mocker: MockerFixture) -> None:
        failure = RunScriptInvalidExitCode(
            artifact_id=ArtifactId("@/workflow.donna.md"), section_id=SectionId("script"), exit_code="invalid"
        )
        mocker.patch("donna.cli.utils.locate_config", return_value=Err([failure]))

        result = helpers.invoke(["-p", "automation", "list"])

        assert result.exit_code == 3
        assert not result.stderr
        record = helpers.json_lines(result.stdout)[0]
        assert record["code"] == failure.code
        assert record["exit_code"] == "invalid"
        assert "cli_exit_code" not in record
        assert failure.format_message() in str(record["content"])

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    @pytest.mark.parametrize(
        "payload",
        [
            config_errors.Unreadable(path=pathlib.Path("/config.toml"), reason="denied"),
            (config_errors.Unreadable(path=pathlib.Path("/config.toml"), reason="denied"),),
            [config_errors.Unreadable(path=pathlib.Path("/config.toml"), reason="denied"), "unexpected payload"],
        ],
    )
    def test_unrecognized_unwrap_payload__is_not_silently_dropped(
        self, mocker: MockerFixture, protocol: str, payload: object
    ) -> None:
        failure = UnwrapError(error=[])
        failure.details["error"] = payload
        mocker.patch("donna.cli.utils.locate_config", side_effect=failure)

        result = helpers.invoke(["-p", protocol, "list"])

        assert result.exception == failure
        assert result.exit_code != 0
        assert not result.stdout
        assert not result.stderr

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
