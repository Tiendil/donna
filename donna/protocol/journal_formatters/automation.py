from llm_tool_cli.protocol import to_jsonl

from donna.protocol.journal import JournalRecord
from donna.protocol.journal_formatters.base import Formatter as BaseFormatter


class Formatter(BaseFormatter):
    __slots__ = ()

    def format_journal(self, record: JournalRecord) -> bytes:
        return to_jsonl(record.model_dump(mode="json")).encode("utf-8")
