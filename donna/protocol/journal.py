import datetime
import json

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.artifact_ids import ArtifactSectionId
from donna.domain.internal_ids import TaskId, WorkUnitId


def message_has_newlines(message: str) -> bool:
    return "\n" in message or "\r" in message


class JournalRecord(BaseEntity):
    timestamp: datetime.datetime
    actor_id: str | None
    message: str
    current_task_id: TaskId | None
    current_work_unit_id: WorkUnitId | None
    current_operation_id: ArtifactSectionId | None

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
