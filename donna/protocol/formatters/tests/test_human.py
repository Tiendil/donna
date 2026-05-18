from donna.protocol.formatters.human import Formatter
from donna.protocol.tests.make import cell, journal_record


class TestFormatter:
    def test_format_cell__renders_human_cell_with_sorted_metadata(self) -> None:
        formatted = Formatter().format_cell(cell()).decode()

        assert formatted == (
            "----- DONNA CELL EjRWeBI0VniSNFZ4EjRWeA -----\n"
            "kind = sample_status\n"
            "media_type = text/markdown\n"
            "alpha = first\n"
            "enabled = True\n"
            "missing = None\n"
            "zeta = 2\n"
            "\n"
            "Sample content.\n"
            "\n"
        )

    def test_format_cell__omits_media_type_and_content_when_absent(self) -> None:
        formatted = Formatter().format_cell(cell(media_type=None, content=None, meta={})).decode()

        assert formatted == "----- DONNA CELL EjRWeBI0VniSNFZ4EjRWeA -----\nkind = sample_status\n\n"

    def test_format_journal__renders_time_short_task_actor_and_message(self) -> None:
        formatted = Formatter().format_journal(journal_record()).decode()

        assert formatted == "10:30:45 [42] <agent> Completed step"

    def test_format_journal__uses_placeholders_for_missing_optional_fields(self) -> None:
        formatted = Formatter().format_journal(journal_record(actor_id=None, current_task_id=None)).decode()

        assert formatted == "10:30:45 [-] <-> Completed step"
