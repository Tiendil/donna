from donna.machine.journal import JournalRecord
from donna.protocol.cells import Cell
from donna.protocol.formatters.base import Formatter as BaseFormatter


class Formatter(BaseFormatter):

    def format_cell(self, cell: Cell, single_mode: bool) -> bytes:  # noqa: CCR001
        id = cell.short_id

        lines = []

        if not single_mode:
            lines = [f"--DONNA-CELL {id} BEGIN--"]

        lines.append(f"kind={cell.kind}")

        if cell.media_type is not None:
            lines.append(f"media_type={cell.media_type}")

        for meta_key, meta_value in sorted(cell.meta.items()):
            lines.append(f"{meta_key}={meta_value}")

        if cell.content:
            lines.append("")
            lines.append(cell.content.strip())

        if not single_mode:
            lines.append(f"--DONNA-CELL {id} END--")

        return "\n".join(lines).strip().encode()

    def format_journal(self, record: JournalRecord) -> bytes:
        timestamp = record.timestamp.isoformat()
        actor_id = record.actor_id or "-"
        current_task_id = record.current_task_id or "-"
        current_work_unit_id = record.current_work_unit_id or "-"
        current_operation_id = record.current_operation_id or "-"

        output = (
            f"{timestamp} "
            f"[{actor_id}] "
            f"[{current_task_id}] "
            f"[{current_work_unit_id}] "
            f"[{current_operation_id}] "
            f"{record.message}"
        )
        return output.encode()

    def format_cells(self, cells: list[Cell]) -> bytes:
        single_mode = len(cells) == 1
        formatted_cells = [self.format_cell(cell, single_mode=single_mode) for cell in cells]
        return b"\n\n".join(formatted_cells)
