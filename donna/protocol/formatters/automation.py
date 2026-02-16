import json

from donna.machine.journal import JournalRecord, serialize_record
from donna.protocol.cells import Cell
from donna.protocol.formatters.base import Formatter as BaseFormatter


class Formatter(BaseFormatter):

    def format_cell(self, cell: Cell) -> bytes:
        data: dict[str, str | int | bool | None] = {"id": cell.short_id}

        for meta_key, meta_value in sorted(cell.meta.items()):
            data[meta_key] = meta_value

        data["content"] = cell.content.strip() if cell.content else None

        return json.dumps(data, ensure_ascii=False, indent=None, separators=(",", ":"), sort_keys=True).encode()

    def format_journal(self, record: JournalRecord) -> bytes:
        return serialize_record(record)
