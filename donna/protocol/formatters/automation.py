from llm_tool_cli.core.errors import EnvironmentError
from llm_tool_cli.protocol import to_jsonl
from llm_tool_cli.protocol.cells import Cell, MetaValue

from donna.protocol.formatters.base import Formatter as BaseFormatter
from donna.protocol.journal import JournalRecord


class Formatter(BaseFormatter):

    def format_error(self, error: EnvironmentError) -> bytes:
        return to_jsonl(error.as_record()).encode("utf-8")

    def format_cell(self, cell: Cell) -> bytes:
        data: dict[str, MetaValue] = {"id": cell.short_id}

        for meta_key, meta_value in sorted(cell.meta.items()):
            data[meta_key] = meta_value

        data["content"] = cell.content.strip() if cell.content else None

        return to_jsonl(data).encode("utf-8")

    def format_journal(self, record: JournalRecord) -> bytes:
        return to_jsonl(record.model_dump(mode="json")).encode("utf-8")
