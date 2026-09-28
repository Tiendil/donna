from donna.protocol.journal_formatters.llm import Formatter
from donna.protocol.tests.make import journal_record


class TestFormatter:
    def test_format_journal__renders_full_journal_context(self) -> None:
        formatted = Formatter().format_journal(journal_record()).decode()

        assert formatted == (
            "2026-05-18T10:30:45+00:00 [task-42-Q] <agent> "
            "[work-unit-7-h] [@/workflow.donna.md:operation] Completed step\n"
        )

    def test_format_journal__uses_placeholders_for_missing_optional_fields(self) -> None:
        formatted = (
            Formatter()
            .format_journal(
                journal_record(
                    actor_id=None,
                    current_task_id=None,
                    current_work_unit_id=None,
                    current_operation_id=None,
                )
            )
            .decode()
        )

        assert formatted == "2026-05-18T10:30:45+00:00 [-] <-> [-] [-] Completed step\n"
