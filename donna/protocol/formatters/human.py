from donna.machine.journal import JournalRecord
from donna.protocol.cells import Cell
from donna.protocol.formatters.base import Formatter as BaseFormatter


class Formatter(BaseFormatter):

    def format_cell(self, cell: Cell) -> bytes:
        id = cell.short_id

        lines = [f"----- DONNA CELL {id} -----"]

        lines.append(f"kind = {cell.kind}")

        if cell.media_type is not None:
            lines.append(f"media_type = {cell.media_type}")

        for meta_key, meta_value in sorted(cell.meta.items()):
            lines.append(f"{meta_key} = {meta_value}")

        if cell.content:
            lines.append("")
            lines.append(cell.content.strip())

        return "\n".join(lines).encode()

    def format_journal(self, record: JournalRecord) -> bytes:
        timestamp = record.timestamp.time().isoformat("seconds")
        actor_id = record.actor_id or "-"
        current_task_id = record.current_task_id.short if record.current_task_id is not None else "-"
        output = f"{timestamp} [{current_task_id}] <{actor_id}> {record.message}"
        return output.encode()
