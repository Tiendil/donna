from __future__ import annotations

import subprocess  # noqa: S404
from typing import TYPE_CHECKING

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.workspaces import errors as workspace_errors
from donna.workspaces.config import JournalRecordAttribute

if TYPE_CHECKING:
    from donna.protocol.journal import JournalRecord


def _is_variable_argument(argument: str) -> bool:
    return len(argument) >= 2 and argument[0] == "{" and argument[-1] == "}"


def _parse_record_attribute(name: str, argument: str) -> Result[JournalRecordAttribute, ErrorsList]:
    if not JournalRecordAttribute.has_attribute(name):
        return Err(
            [
                workspace_errors.JournalCommandConfigInvalid(
                    argument=argument,
                    details=f"`{name}` is not a supported `JournalRecord` argument.",
                )
            ]
        )

    return Ok(JournalRecordAttribute[name])


def _format_record_attribute(attribute: JournalRecordAttribute, record: JournalRecord) -> str:
    match attribute:
        case JournalRecordAttribute.timestamp:
            return record.timestamp.isoformat()
        case JournalRecordAttribute.actor_id:
            return record.actor_id or ""
        case JournalRecordAttribute.message:
            return record.message
        case JournalRecordAttribute.current_task_id:
            return str(record.current_task_id) if record.current_task_id is not None else ""
        case JournalRecordAttribute.current_work_unit_id:
            return str(record.current_work_unit_id) if record.current_work_unit_id is not None else ""
        case JournalRecordAttribute.current_operation_id:
            return str(record.current_operation_id) if record.current_operation_id is not None else ""

    raise AssertionError(f"Unsupported journal record attribute: {attribute}")


def _resolve_command_argument(argument: str, record: JournalRecord) -> Result[str, ErrorsList]:
    if not _is_variable_argument(argument):
        return Ok(argument)

    name = argument[1:-1]
    attribute = _parse_record_attribute(name, argument).unwrap()
    return Ok(_format_record_attribute(attribute, record))


@unwrap_to_error
def _build_command_args(command: list[str], record: JournalRecord) -> Result[list[str], ErrorsList]:
    args = []

    for argument in command:
        args.append(_resolve_command_argument(argument, record).unwrap())

    return Ok(args)


@unwrap_to_error
def write_record(record: JournalRecord) -> Result[None, ErrorsList]:
    from donna.workspaces import config as workspace_config

    command = workspace_config.config().journal.cmd
    if command is None:
        return Ok(None)

    args = _build_command_args(command, record).unwrap()

    try:
        result = subprocess.run(args, check=False, capture_output=True, text=True)  # noqa: S603
    except OSError as e:
        return Err(
            [
                workspace_errors.JournalCommandFailed(
                    command=args,
                    returncode=None,
                    details=str(e),
                )
            ]
        )

    if result.returncode != 0:
        details = f"exit code {result.returncode}"
        stderr = result.stderr.strip()
        if stderr:
            details = f"{details}; stderr: {stderr}"

        return Err(
            [
                workspace_errors.JournalCommandFailed(
                    command=args,
                    returncode=result.returncode,
                    details=details,
                )
            ]
        )

    return Ok(None)
