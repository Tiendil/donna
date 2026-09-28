from donna.protocol.journal_formatters.automation import Formatter
from donna.protocol.tests.make import journal_record


class TestFormatter:
    def test_format_journal__serializes_journal_record_as_json_line(self) -> None:
        formatted = Formatter().format_journal(journal_record())

        assert formatted == (
            b'{"actor_id":"agent","current_operation_id":"@/workflow.donna.md:operation",'
            b'"current_task_id":"task-42-Q","current_work_unit_id":"work-unit-7-h",'
            b'"message":"Completed step","timestamp":"2026-05-18T10:30:45Z"}\n'
        )
