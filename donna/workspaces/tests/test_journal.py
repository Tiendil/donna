import subprocess  # noqa: S404

from donna.workspaces import errors as workspace_errors
from donna.workspaces import journal
from donna.workspaces.config import Config, JournalConfig, JournalRecordAttribute
from donna.workspaces.tests import make


class TestIsVariableArgument:
    def test_detects_whole_argument_placeholders(self) -> None:
        assert journal._is_variable_argument("{message}")
        assert not journal._is_variable_argument("literal:{message}")
        assert not journal._is_variable_argument("{message")


class TestParseRecordAttribute:
    def test_returns_supported_attribute(self) -> None:
        result = journal._parse_record_attribute("message", "{message}")

        assert result.is_ok()
        assert result.unwrap() == JournalRecordAttribute.message

    def test_reports_unsupported_attribute(self) -> None:
        result = journal._parse_record_attribute("missing", "{missing}")

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.JournalCommandConfigInvalid)
        assert error.argument == "{missing}"


class TestFormatRecordAttribute:
    def test_formats_record_attributes(self) -> None:
        record = make.journal_record()

        assert (
            journal._format_record_attribute(JournalRecordAttribute.timestamp, record) == "2026-05-18T10:30:00+00:00"
        )
        assert journal._format_record_attribute(JournalRecordAttribute.actor_id, record) == "agent"
        assert journal._format_record_attribute(JournalRecordAttribute.message, record) == "message"
        assert journal._format_record_attribute(JournalRecordAttribute.current_task_id, record) == "T-1-b"
        assert journal._format_record_attribute(JournalRecordAttribute.current_work_unit_id, record) == "WU-2-c"
        assert (
            journal._format_record_attribute(JournalRecordAttribute.current_operation_id, record)
            == "@/workflows/test.donna.md:primary"
        )

    def test_formats_missing_optional_attributes_as_empty_strings(self) -> None:
        record = make.journal_record(
            actor_id=None,
            current_task_id=None,
            current_work_unit_id=None,
            current_operation_id=None,
        )

        assert journal._format_record_attribute(JournalRecordAttribute.actor_id, record) == ""
        assert journal._format_record_attribute(JournalRecordAttribute.current_task_id, record) == ""
        assert journal._format_record_attribute(JournalRecordAttribute.current_work_unit_id, record) == ""
        assert journal._format_record_attribute(JournalRecordAttribute.current_operation_id, record) == ""


class TestResolveCommandArgument:
    def test_returns_literal_argument(self) -> None:
        result = journal._resolve_command_argument("literal:{message}", make.journal_record())

        assert result.is_ok()
        assert result.unwrap() == "literal:{message}"

    def test_resolves_placeholder_argument(self) -> None:
        result = journal._resolve_command_argument("{message}", make.journal_record())

        assert result.is_ok()
        assert result.unwrap() == "message"


class TestBuildCommandArgs:
    def test_replaces_whole_argument_placeholders(self) -> None:
        record = make.journal_record()

        result = journal._build_command_args(
            [
                "tool",
                "{timestamp}",
                "{actor_id}",
                "{current_task_id}",
                "{current_work_unit_id}",
                "{current_operation_id}",
                "{message}",
                "literal:{message}",
            ],
            record,
        )

        assert result.is_ok()
        assert result.unwrap() == [
            "tool",
            "2026-05-18T10:30:00+00:00",
            "agent",
            "T-1-b",
            "WU-2-c",
            "@/workflows/test.donna.md:primary",
            "message",
            "literal:{message}",
        ]

    def test_replaces_missing_optional_record_values_with_empty_strings(self) -> None:
        record = make.journal_record(
            actor_id=None,
            current_task_id=None,
            current_work_unit_id=None,
            current_operation_id=None,
        )

        result = journal._build_command_args(
            ["{actor_id}", "{current_task_id}", "{current_work_unit_id}", "{current_operation_id}"],
            record,
        )

        assert result.is_ok()
        assert result.unwrap() == ["", "", "", ""]

    def test_unsupported_placeholder_returns_config_error(self) -> None:
        result = journal._build_command_args(["{missing}"], make.journal_record())

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.JournalCommandConfigInvalid)
        assert error.argument == "{missing}"


class TestWriteRecord:
    def test_no_configured_command_is_noop(self, mocker: object) -> None:
        mocker.patch(
            "donna.workspaces.config.config",
            return_value=Config(journal=JournalConfig(cmd=None)),
        )
        run = mocker.patch("subprocess.run")

        result = journal.write_record(make.journal_record())

        assert result.is_ok()
        run.assert_not_called()

    def test_runs_configured_command(self, mocker: object) -> None:
        mocker.patch(
            "donna.workspaces.config.config",
            return_value=Config(journal=JournalConfig(cmd=["tool", "{message}"])),
        )
        run = mocker.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(args=["tool", "message"], returncode=0, stdout="", stderr=""),
        )

        result = journal.write_record(make.journal_record())

        assert result.is_ok()
        run.assert_called_once_with(["tool", "message"], check=False, capture_output=True, text=True)

    def test_reports_command_os_error(self, mocker: object) -> None:
        mocker.patch(
            "donna.workspaces.config.config",
            return_value=Config(journal=JournalConfig(cmd=["tool"])),
        )
        mocker.patch("subprocess.run", side_effect=OSError("missing"))

        result = journal.write_record(make.journal_record())

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.JournalCommandFailed)
        assert error.command == ["tool"]
        assert error.returncode is None

    def test_reports_nonzero_command_exit(self, mocker: object) -> None:
        mocker.patch(
            "donna.workspaces.config.config",
            return_value=Config(journal=JournalConfig(cmd=["tool"])),
        )
        mocker.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(args=["tool"], returncode=2, stdout="", stderr="bad"),
        )

        result = journal.write_record(make.journal_record())

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.JournalCommandFailed)
        assert error.command == ["tool"]
        assert error.returncode == 2
        assert error.details == "exit code 2; stderr: bad"
