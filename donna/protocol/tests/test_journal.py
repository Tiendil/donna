import json

import pydantic
import pytest

from donna.protocol.journal import JournalRecord, message_has_newlines, serialize_record
from donna.protocol.tests.make import journal_record


class TestMessageHasNewlines:
    @pytest.mark.parametrize("message", ("line\nnext", "line\rnext"))
    def test_detects_newline_characters(self, message: str) -> None:
        assert message_has_newlines(message)

    def test_returns_false_for_single_line_message(self) -> None:
        assert not message_has_newlines("single line")


class TestJournalRecord:
    @pytest.mark.parametrize("message", ("line\nnext", "line\rnext"))
    def test_validate_message_no_newlines__rejects_multiline_message(self, message: str) -> None:
        with pytest.raises(pydantic.ValidationError):
            JournalRecord.model_validate(
                {
                    **journal_record().model_dump(),
                    "message": message,
                }
            )


class TestSerializeRecord:
    def test_serializes_record_as_sorted_compact_json(self) -> None:
        record = journal_record()

        serialized = serialize_record(record)

        assert json.loads(serialized) == {
            "actor_id": "agent",
            "current_operation_id": "@/workflow.donna.md:operation",
            "current_task_id": "task-42-Q",
            "current_work_unit_id": "work-unit-7-h",
            "message": "Completed step",
            "timestamp": "2026-05-18T10:30:45Z",
        }
        assert serialized == (
            b'{"actor_id":"agent","current_operation_id":"@/workflow.donna.md:operation",'
            b'"current_task_id":"task-42-Q","current_work_unit_id":"work-unit-7-h",'
            b'"message":"Completed step","timestamp":"2026-05-18T10:30:45Z"}'
        )
