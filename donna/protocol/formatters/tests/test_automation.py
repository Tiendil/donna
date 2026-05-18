import json

from donna.protocol.formatters.automation import Formatter
from donna.protocol.tests.make import cell, journal_record


class TestFormatter:
    def test_format_cell__serializes_cell_as_sorted_json_line(self) -> None:
        formatted = Formatter().format_cell(cell())

        assert json.loads(formatted) == {
            "alpha": "first",
            "content": "Sample content.",
            "enabled": True,
            "id": "EjRWeBI0VniSNFZ4EjRWeA",
            "missing": None,
            "zeta": 2,
        }
        assert formatted == (
            b'{"alpha":"first","content":"Sample content.","enabled":true,'
            b'"id":"EjRWeBI0VniSNFZ4EjRWeA","missing":null,"zeta":2}\n'
        )

    def test_format_cell__serializes_missing_content_as_null(self) -> None:
        formatted = Formatter().format_cell(cell(content=None))

        assert json.loads(formatted)["content"] is None

    def test_format_journal__serializes_journal_record_as_json_line(self) -> None:
        formatted = Formatter().format_journal(journal_record())

        assert formatted == (
            b'{"actor_id":"agent","current_operation_id":"@/workflow.donna.md:operation",'
            b'"current_task_id":"task-42-Q","current_work_unit_id":"work-unit-7-h",'
            b'"message":"Completed step","timestamp":"2026-05-18T10:30:45Z"}\n'
        )
