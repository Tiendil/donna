import pathlib
import subprocess  # noqa: S404

import click
import pytest
import typer
from llm_tool_cli.cli.errors import InvalidArguments
from llm_tool_cli.config import errors as config_errors
from llm_tool_cli.config.project import ProjectConfig, project_config
from llm_tool_cli.config.runtime import runtime_config
from llm_tool_cli.config.tests.fixtures import runtime_settings
from llm_tool_cli.core import errors as llm_tool_errors
from llm_tool_cli.core.result import Err, Ok, Result, UnwrapError
from llm_tool_cli.output import OutputEmitter, output
from llm_tool_cli.output.journal import NoopJournalProcessor
from llm_tool_cli.paths import ProjectConfigPath
from llm_tool_cli.protocol import Protocol
from llm_tool_cli.protocol.tests.helpers import assert_error_cells
from pytest_mock import MockerFixture

from donna.cli import utils as cli_utils
from donna.cli.tests import helpers
from donna.context.tests import make as context_make
from donna.context.tests.helpers import FakeOutputEmitter
from donna.domain.artifact_ids import ArtifactId
from donna.domain.ids import SectionId
from donna.machine import Caches, ExecutionContext
from donna.machine.artifacts import Artifact
from donna.machine.caches import caches
from donna.machine.context import execution_context
from donna.machine.tests import make as machine_make
from donna.primitives.sections.run_script import RunScriptInvalidExitCode
from donna.protocol.tests.make import cell
from donna.workspaces import config as workspace_config
from donna.workspaces import errors as workspace_errors


class TestCommandContext:
    @pytest.mark.parametrize(
        ("protocol", "actor"), [("human", "human"), ("llm", "agent"), ("automation", "automation")]
    )
    def test_journal_cells__capture_selected_actor(
        self, mocker: MockerFixture, tmp_path: pathlib.Path, protocol: str, actor: str
    ) -> None:
        config_path = helpers.write_config(tmp_path)
        processed = mocker.spy(NoopJournalProcessor, "process")

        result = helpers.invoke(["--config", str(config_path), "-p", protocol, "new-session"])

        assert result.exit_code == 0, result.exception
        processed.assert_called_once()
        cell = processed.call_args.args[1]
        assert cell.actor_id == actor
        assert cell.message == "Created new session state."
        assert cell.current_task_id is None
        assert cell.current_work_unit_id is None
        assert cell.current_operation_id is None

    def test_journal_processor_failure__does_not_print_or_retry_the_event(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        config_path = helpers.write_config(tmp_path)
        config_path.write_text(config_path.read_text() + '\n[journal]\ncmd = ["journal-tool", "{message}"]\n')
        run = mocker.patch(
            "llm_tool_cli.output.journal.subprocess.run",
            return_value=subprocess.CompletedProcess([], 7, "", "forwarding failed"),
        )

        result = helpers.invoke(["--config", str(config_path), "-p", "automation", "new-session"])

        assert result.exit_code == 3
        run.assert_called_once()
        records = helpers.json_lines(result.stdout)
        assert len(records) == 1
        assert records[0]["code"] == "journal_command_failed"
        assert records[0]["returncode"] == 7
        assert "current_work_unit_id" not in records[0]
        assert not result.stderr

    @pytest.mark.parametrize("outcome", ["success", "environment_error", "exception"])
    def test_runtime_scopes__start_fresh_and_restore_previous_bindings(
        self, mocker: MockerFixture, tmp_path: pathlib.Path, outcome: str
    ) -> None:
        config_path = helpers.write_config(tmp_path)
        initialized = helpers.invoke(["--config", str(config_path), "-p", "automation", "new-session"])
        assert initialized.exit_code == 0
        assert not execution_context.is_set()
        assert not caches.is_set()
        assert not output.is_set()
        observed: list[tuple[ExecutionContext, Caches, OutputEmitter]] = []
        failure = llm_tool_errors.EnvironmentError(code="command_failed", message="Command failed")
        defect = ValueError("unexpected defect")

        def observe(*args: object, **kwargs: object) -> Result[list[Artifact]]:
            observed.append((execution_context.get(), caches.get(), output.get()))
            if outcome == "environment_error":
                Err([failure]).unwrap()
            if outcome == "exception":
                raise defect
            return Ok([])

        mocker.patch("donna.context.artifacts.ArtifactsCache.list", side_effect=observe)
        outer = ExecutionContext(
            current_work_unit_id=machine_make.WORK_UNIT_ID,
            current_operation_id=machine_make.PRIMARY_OPERATION_ID,
        )
        previous_caches = context_make.caches()
        previous_output = FakeOutputEmitter()
        with (
            execution_context.scope(outer),
            caches.scope(previous_caches),
            output.scope(previous_output),
        ):
            result = helpers.invoke(["--config", str(config_path), "-p", "automation", "list"])
            assert execution_context.get() == outer
            assert caches.get() == previous_caches
            assert output.get() == previous_output

        assert len(observed) == 1
        assert observed[0][0] == ExecutionContext()
        assert observed[0][1] != previous_caches
        assert observed[0][2] != previous_output
        assert not execution_context.is_set()
        assert not caches.is_set()
        assert not output.is_set()
        assert not previous_output.cells
        assert not previous_output.journal_records
        if outcome == "success":
            assert result.exit_code == 0, result.exception
        elif outcome == "environment_error":
            assert result.exit_code == 3
            records = helpers.json_lines(result.stdout)
            assert_error_cells([record for record in records if record.get("type") == "error"], [failure])
            journals = [record for record in records if "current_work_unit_id" in record]
            assert len(journals) == 2
            assert journals[0]["current_work_unit_id"] is None
            assert journals[0]["current_operation_id"] is None
        else:
            assert result.exception == defect
            assert [record["message"] for record in helpers.json_lines(result.stdout)] == ["List artifacts"]
            assert not result.stderr

    def test_failed_preparation__does_not_create_caches_or_use_journal(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        construct = mocker.spy(cli_utils, "Caches")
        previous = context_make.caches()
        previous_output = FakeOutputEmitter()
        with caches.scope(previous), output.scope(previous_output):
            result = helpers.invoke(["--config", str(tmp_path / "missing.toml"), "-p", "automation", "list"])
            assert caches.get() == previous
            assert output.get() == previous_output

        assert result.exit_code == 2
        construct.assert_not_called()
        assert not caches.is_set()
        assert not output.is_set()

    def test_output_scope__works_without_workspace_and_restores_outer_emitter(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        previous_output = FakeOutputEmitter()
        cli_context = typer.Context(click.Command("init"))
        with output.scope(previous_output), cli_context:
            with cli_utils.command_context(cli_context, load_environment=False):
                assert not caches.is_set()
                assert not execution_context.is_set()
                output.get().emit([cell(content="Without a workspace")]).unwrap()
            cli_context.close()
            assert output.get() == previous_output

        assert "Without a workspace" in capsys.readouterr().out
        assert not previous_output.cells
        assert not output.is_set()

    @pytest.mark.parametrize("command", ["init", "skill", "version"])
    def test_project_independent_commands__do_not_create_caches_or_journal(
        self, mocker: MockerFixture, tmp_path: pathlib.Path, command: str
    ) -> None:
        construct = mocker.spy(cli_utils, "Caches")
        result = helpers.invoke(["--config", str(tmp_path / "donna.toml"), "-p", "automation", command])

        assert result.exit_code == 0, result.exception
        construct.assert_not_called()
        assert not caches.is_set()
        assert not output.is_set()

    def test_workspace_setup__keeps_runtime_and_loaded_settings_together(
        self, mocker: MockerFixture, tmp_path: pathlib.Path
    ) -> None:
        observed: list[tuple[Protocol, pathlib.Path, pathlib.Path, pathlib.Path]] = []

        def observe(*args: object, **kwargs: object) -> Result[list[Artifact]]:
            project = project_config.get()
            observed.append(
                (
                    runtime_config.get().protocol,
                    project.config_path,
                    project.project_dir,
                    workspace_config.config.get().session_dir,
                )
            )
            return Ok([])

        mocker.patch("donna.context.artifacts.ArtifactsCache.list", side_effect=observe)
        outer = runtime_config.get()
        outer_project = ProjectConfig(config_path=ProjectConfigPath(tmp_path / "outer.toml"))
        previous = workspace_config.Config()
        with project_config.scope(outer_project), workspace_config.config.scope(previous):
            for name, protocol in [("first", Protocol.llm), ("second", Protocol.automation)]:
                root = tmp_path / name
                root.mkdir()
                config_path = root / "custom.toml"
                config_path.write_text(f'session_dir = "{name}"\nworkflow_dirs = []\n', encoding="utf-8")

                result = helpers.invoke(["--config", str(config_path), "-p", protocol.value, "list"])

                assert result.exit_code == 0, result.exception
                assert observed[-1] == (protocol, config_path, root, pathlib.Path(name))
                assert runtime_config.get() == outer
                assert project_config.get() == outer_project
                assert workspace_config.config.get() == previous

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
            assert not result.stderr
            separator = " = " if protocol == "human" else "="
            assert f"kind{separator}error\n" in result.stdout
            assert f"code{separator}{code}\n" in result.stdout
            assert f"path{separator}{tmp_path}\n" in result.stdout

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
        mocker.patch("llm_tool_cli.config.project.locate_config", return_value=Err([error]))

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
            assert not result.stderr
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
    def test_shared_config_errors__write_cells_to_stdout(
        self, mocker: MockerFixture, tmp_path: pathlib.Path, protocol: str
    ) -> None:
        failure = config_errors.DiscoveryFailed(path=tmp_path, reason="permission denied")
        mocker.patch("llm_tool_cli.config.project.locate_config", return_value=Err([failure]))

        result = helpers.invoke(["-p", protocol, "list"])

        assert result.exit_code == 2
        assert not result.stderr
        assert result.stdout.startswith("----- DONNA CELL " if protocol == "human" else "--DONNA-CELL ")
        assert failure.format_message() in result.stdout
        assert ("kind = error" if protocol == "human" else "kind=error") in result.stdout

    def test_other_shared_errors__preserve_record_and_exit_three(self, mocker: MockerFixture) -> None:
        failure = llm_tool_errors.EnvironmentError(message="service unavailable", code="service_unavailable")
        mocker.patch("llm_tool_cli.config.project.locate_config", return_value=Err([failure]))

        result = helpers.invoke(["-p", "automation", "list"])

        assert result.exit_code == 3
        assert_error_cells(helpers.json_lines(result.stdout), [failure])
        assert not result.stderr

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    def test_invalid_arguments__use_declared_exit_code(self, mocker: MockerFixture, protocol: str) -> None:
        failure = InvalidArguments(reason="invalid argument")
        mocker.patch("llm_tool_cli.config.project.locate_config", return_value=Err([failure]))

        result = helpers.invoke(["-p", protocol, "list"])

        assert result.exit_code == 1
        if protocol == "automation":
            assert_error_cells(helpers.json_lines(result.stdout), [failure])
            assert not result.stderr
        else:
            assert not result.stderr
            separator = " = " if protocol == "human" else "="
            assert f"code{separator}invalid_arguments\n" in result.stdout

    @pytest.mark.parametrize("with_session", [False, True])
    @pytest.mark.parametrize(
        ("message", "journal_message"),
        [("command failed", "command failed"), ("First line.\nSecond line.", "First line. Second line.")],
    )
    def test_shared_errors_during_command__restore_output_scope(
        self, mocker: MockerFixture, tmp_path: pathlib.Path, with_session: bool, message: str, journal_message: str
    ) -> None:
        config_path = helpers.write_config(tmp_path)
        if with_session:
            initialized = helpers.invoke(["--config", str(config_path), "-p", "automation", "new-session"])
            assert initialized.exit_code == 0
        failure = llm_tool_errors.EnvironmentError(message=message, code="command_failed")
        mocker.patch("donna.context.artifacts.ArtifactsCache.list", side_effect=UnwrapError(error=[failure]))
        forwarded = mocker.spy(NoopJournalProcessor, "process")
        previous_output = FakeOutputEmitter()
        with output.scope(previous_output):
            result = helpers.invoke(["--config", str(config_path), "-p", "automation", "list"])

            assert result.exit_code == 3
            records = helpers.json_lines(result.stdout)
            assert_error_cells([record for record in records if record.get("type") == "error"], [failure])
            assert forwarded.call_count == 2
            journal_entry = forwarded.call_args.args[1]
            assert journal_entry.actor_id == "donna"
            assert journal_entry.current_task_id is None
            assert journal_entry.message == f"Error: {journal_message} [{failure.code}]"
            assert output.get() == previous_output
            assert not previous_output.journal_records
            assert not project_config.is_set()

    def test_unexpected_errors__propagate_without_expected_diagnostic(self, mocker: MockerFixture) -> None:
        failure = RuntimeError("unexpected defect")
        mocker.patch("llm_tool_cli.config.project.locate_config", side_effect=failure)

        result = helpers.invoke(["-p", "automation", "list"])

        assert result.exception == failure
        assert not result.stdout
        assert not result.stderr

    def test_shared_internal_errors__propagate_without_expected_diagnostic(self, mocker: MockerFixture) -> None:
        failure = llm_tool_errors.InternalError("unexpected defect")
        mocker.patch("llm_tool_cli.config.project.locate_config", side_effect=failure)

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
        mocker.patch("llm_tool_cli.config.project.locate_config", return_value=Err(failures))

        result = helpers.invoke(["-p", protocol, "list"])

        assert result.exit_code == 3
        if protocol == "automation":
            records = helpers.json_lines(result.stdout)
            assert [record["code"] for record in records] == [error.code for error in failures]
            assert records[failures.index(local)]["artifact_id"] == local.artifact_id
            assert all("cli_exit_code" not in record for record in records)
            assert not result.stderr
        else:
            assert not result.stderr
            separator = " = " if protocol == "human" else "="
            codes = [f"code{separator}{error.code}\n" for error in failures]
            assert all(code in result.stdout for code in codes)
            positions = [result.stdout.index(code) for code in codes]
            assert positions == sorted(positions)

    def test_script_exit_code_context__does_not_override_cli_exit_code(self, mocker: MockerFixture) -> None:
        failure = RunScriptInvalidExitCode(
            artifact_id=ArtifactId("@/workflow.donna.md"), section_id=SectionId("script"), exit_code="invalid"
        )
        mocker.patch("llm_tool_cli.config.project.locate_config", return_value=Err([failure]))

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
        mocker.patch("llm_tool_cli.config.project.locate_config", side_effect=failure)

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
            assert not result.stderr
            assert "donna.toml" in result.stdout
            assert str(tmp_path) in result.stdout


__all__ = ["runtime_settings"]

pytestmark = pytest.mark.usefixtures("runtime_settings")
