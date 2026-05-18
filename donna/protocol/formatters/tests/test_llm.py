from donna.protocol.formatters.llm import Formatter
from donna.protocol.tests.make import cell, journal_record


class TestFormatter:
    def test_format_cell__renders_llm_cell_with_sorted_metadata(self) -> None:
        formatted = Formatter().format_cell(cell()).decode()

        assert formatted == (
            "--DONNA-CELL EjRWeBI0VniSNFZ4EjRWeA BEGIN--\n"
            "kind=sample_status\n"
            "media_type=text/markdown\n"
            "alpha=first\n"
            "enabled=True\n"
            "missing=None\n"
            "zeta=2\n"
            "\n"
            "Sample content.\n"
            "--DONNA-CELL EjRWeBI0VniSNFZ4EjRWeA END--\n"
        )

    def test_format_cell__omits_media_type_and_content_when_absent(self) -> None:
        formatted = Formatter().format_cell(cell(media_type=None, content=None, meta={})).decode()

        assert formatted == (
            "--DONNA-CELL EjRWeBI0VniSNFZ4EjRWeA BEGIN--\n"
            "kind=sample_status\n"
            "--DONNA-CELL EjRWeBI0VniSNFZ4EjRWeA END--\n"
        )

    def test_format_journal__renders_full_journal_context(self) -> None:
        formatted = Formatter().format_journal(journal_record()).decode()

        assert formatted == (
            "2026-05-18T10:30:45+00:00 [task-42-Q] <agent> "
            "[work-unit-7-h] [@/workflow.donna.md:operation] Completed step"
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

        assert formatted == "2026-05-18T10:30:45+00:00 [-] <-> [-] [-] Completed step"
