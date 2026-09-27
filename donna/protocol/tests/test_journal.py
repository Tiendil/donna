import pydantic
import pytest

from donna.protocol.journal import JournalRecord, message_has_newlines
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
