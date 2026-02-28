import datetime
import json
from collections.abc import Iterable

import pydantic

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.core.utils import now
from donna.domain.ids import FullArtifactSectionId, TaskId, WorkUnitId
from donna.machine import errors as machine_errors
from donna.workspaces import utils as workspace_utils
from donna.workspaces.config import protocol as protocol_mode


def message_has_newlines(message: str) -> bool:
    return "\n" in message or "\r" in message


class JournalRecord(BaseEntity):
    timestamp: datetime.datetime
    actor_id: str | None
    message: str
    current_task_id: TaskId | None
    current_work_unit_id: WorkUnitId | None
    current_operation_id: FullArtifactSectionId | None

    @pydantic.field_validator("message", mode="after")
    @classmethod
    def validate_message_no_newlines(cls, value: str) -> str:
        if message_has_newlines(value):
            raise ValueError("Journal message must not contain newline characters.")

        return value


def serialize_record(record: JournalRecord) -> bytes:
    return json.dumps(
        record.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def deserialize_record(content: bytes) -> JournalRecord:
    payload = json.loads(content.decode("utf-8").strip())
    return JournalRecord.model_validate(payload)


@unwrap_to_error
def reset() -> Result[None, ErrorsList]:
    workspace_utils.session_world().unwrap().journal_reset().unwrap()
    return Ok(None)


def smart_agent_id() -> str:
    from donna.protocol.modes import Mode as ProtocolMode

    match protocol_mode():
        case ProtocolMode.human:
            return "human"
        case ProtocolMode.llm:
            return "agent"
        case ProtocolMode.automation:
            return "automation"
        case _:
            raise machine_errors.UnsupportedFormatterMode(mode=protocol_mode())


@unwrap_to_error
def add(  # noqa: CCR001
    message: str,
    actor_id: str | None = None,
) -> Result[JournalRecord, ErrorsList]:
    from donna.context.context import context
    from donna.protocol.utils import instant_output_journal

    if message_has_newlines(message):
        return Err([machine_errors.JournalMessageContainsNewlines()])

    if actor_id is None:
        actor_id = smart_agent_id()

    ctx = context()
    state = ctx.state.load().unwrap()
    parsed_task_id: TaskId | None = state.current_task.id if state.current_task else None
    parsed_work_unit_id: WorkUnitId | None = ctx.current_work_unit_id.get()
    parsed_operation_id: FullArtifactSectionId | None = ctx.current_operation_id.get()

    record = JournalRecord(
        timestamp=now(),
        actor_id=actor_id,
        message=message,
        current_task_id=parsed_task_id,
        current_work_unit_id=parsed_work_unit_id,
        current_operation_id=parsed_operation_id,
    )

    serialized = serialize_record(record)
    workspace_utils.session_world().unwrap().journal_add(serialized).unwrap()

    instant_output_journal(record)

    return Ok(record)


def read(lines: int | None = None, follow: bool = False) -> Iterable[Result[JournalRecord, ErrorsList]]:
    session_world_result = workspace_utils.session_world()
    if session_world_result.is_err():
        yield Err(session_world_result.unwrap_err())
        return

    raw_records = session_world_result.unwrap().journal_read(lines=lines, follow=follow)
    for raw_record_result in raw_records:
        if raw_record_result.is_err():
            yield Err(raw_record_result.unwrap_err())
            continue

        yield Ok(deserialize_record(raw_record_result.unwrap()))
