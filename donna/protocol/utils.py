import sys

from donna.protocol.cells import Cell
from donna.protocol.modes import get_cell_formatter


def _to_optional_string(value: object | None) -> str | None:
    if value is None:
        return None

    return str(value)


def _append_journal_for_log(cell: Cell) -> None:
    from donna.machine import journal as machine_journal

    message = cell.content.strip() if cell.content else ""
    current_task_id = _to_optional_string(cell.meta.get("current_task_id"))
    current_work_unit_id = _to_optional_string(cell.meta.get("current_work_unit_id"))

    result = machine_journal.add(
        actor_id="donna",
        message=message,
        current_task_id=current_task_id,
        current_work_unit_id=current_work_unit_id,
    )

    if result.is_err():
        return


def instant_output(cells: list[Cell]) -> None:
    if not cells:
        return

    formatter = get_cell_formatter()

    formatted_cells: list[bytes] = []
    for cell in cells:
        # TODO: we should refactor that hardcoded check somehow
        if cell.kind == "donna_log":
            _append_journal_for_log(cell)
            formatted_cells.append(formatter.format_log(cell, single_mode=True))
        else:
            formatted_cells.append(formatter.format_cell(cell, single_mode=False))

    sys.stdout.buffer.write(b"\n\n".join(formatted_cells) + b"\n\n")
    sys.stdout.buffer.flush()
