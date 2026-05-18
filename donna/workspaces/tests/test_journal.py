import datetime
import subprocess  # noqa: S404

from pytest_mock import MockerFixture

from donna.domain.artifact_ids import ArtifactSectionId
from donna.domain.internal_ids import TaskId, WorkUnitId
from donna.protocol.journal import JournalRecord
from donna.protocol.tests import make as protocol_make
from donna.workspaces import errors as workspace_errors
from donna.workspaces import journal
from donna.workspaces.config import Config, JournalConfig, JournalRecordAttribute


def _journal_record(**kwargs: object) -> JournalRecord:
    values = {
        "timestamp": datetime.datetime(2026, 5, 18, 10, 30, tzinfo=datetime.UTC),
        "actor_id": "agent",
        "message": "message",
        "current_task_id": TaskId("T-1-b"),
        "current_work_unit_id": WorkUnitId("WU-2-c"),
        "current_operation_id": ArtifactSectionId("@/workflows/test.donna.md:primary"),
    }
    values.update(kwargs)
    return protocol_make.journal_record(**values)


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
        record = _journal_record()

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
        record = _journal_record(
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
        result = journal._resolve_command_argument("literal:{message}", _journal_record())

        assert result.is_ok()
        assert result.unwrap() == "literal:{message}"

    def test_resolves_placeholder_argument(self) -> None:
        result = journal._resolve_command_argument("{message}", _journal_record())

        assert result.is_ok()
        assert result.unwrap() == "message"


class TestBuildCommandArgs:
    def test_replaces_whole_argument_placeholders(self) -> None:
        record = _journal_record()

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
        record = _journal_record(
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
        result = journal._build_command_args(["{missing}"], _journal_record())

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.JournalCommandConfigInvalid)
        assert error.argument == "{missing}"


class TestWriteRecord:
    def test_no_configured_command_is_noop(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "donna.workspaces.config.config",
            return_value=Config(journal=JournalConfig(cmd=None)),
        )
        run = mocker.patch("subprocess.run")

        result = journal.write_record(_journal_record())

        assert result.is_ok()
        run.assert_not_called()

    def test_runs_configured_command(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "donna.workspaces.config.config",
            return_value=Config(journal=JournalConfig(cmd=["tool", "{message}"])),
        )
        run = mocker.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(args=["tool", "message"], returncode=0, stdout="", stderr=""),
        )

        result = journal.write_record(_journal_record())

        assert result.is_ok()
        run.assert_called_once_with(["tool", "message"], check=False, capture_output=True, text=True)

    def test_reports_command_os_error(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "donna.workspaces.config.config",
            return_value=Config(journal=JournalConfig(cmd=["tool"])),
        )
        mocker.patch("subprocess.run", side_effect=OSError("missing"))

        result = journal.write_record(_journal_record())

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.JournalCommandFailed)
        assert error.command == ["tool"]
        assert error.returncode is None

    def test_reports_nonzero_command_exit(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "donna.workspaces.config.config",
            return_value=Config(journal=JournalConfig(cmd=["tool"])),
        )
        mocker.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(args=["tool"], returncode=2, stdout="", stderr="bad"),
        )

        result = journal.write_record(_journal_record())

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, workspace_errors.JournalCommandFailed)
        assert error.command == ["tool"]
        assert error.returncode == 2
        assert error.details == "exit code 2; stderr: bad"
