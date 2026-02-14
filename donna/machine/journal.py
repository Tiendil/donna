import datetime
import json
from collections.abc import Iterable

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.workspaces import utils as workspace_utils


class JournalRecord(BaseEntity):
    timestamp: str
    actor_id: str
    message: str
    current_task_id: str | None = None
    current_work_unit_id: str | None = None
    current_operation_id: str | None = None


def now_timestamp() -> str:
    return datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def serialize_record(record: JournalRecord) -> bytes:
    return json.dumps(
        record.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def deserialize_record(content: bytes) -> JournalRecord:
    return JournalRecord.model_validate_json(content.decode("utf-8").strip())


@unwrap_to_error
def reset() -> Result[None, ErrorsList]:
    workspace_utils.session_world().unwrap().journal_reset().unwrap()
    return Ok(None)


@unwrap_to_error
def add(
    actor_id: str,
    message: str,
    current_task_id: str | None,
    current_work_unit_id: str | None,
    current_operation_id: str | None,
) -> Result[JournalRecord, ErrorsList]:
    record = JournalRecord(
        timestamp=now_timestamp(),
        actor_id=actor_id,
        message=message,
        current_task_id=current_task_id,
        current_work_unit_id=current_work_unit_id,
        current_operation_id=current_operation_id,
    )

    serialized = serialize_record(record)
    workspace_utils.session_world().unwrap().journal_add(serialized).unwrap()
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
