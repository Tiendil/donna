from donna.protocol.journal_formatters.human import Formatter
from donna.protocol.tests.make import journal_record


class TestFormatter:
    def test_format_journal__renders_time_short_task_actor_and_message(self) -> None:
        formatted = Formatter().format_journal(journal_record()).decode()

        assert formatted == "10:30:45 [42] <agent> Completed step\n"

    def test_format_journal__uses_placeholders_for_missing_optional_fields(self) -> None:
        formatted = Formatter().format_journal(journal_record(actor_id=None, current_task_id=None)).decode()

        assert formatted == "10:30:45 [-] <-> Completed step\n"
