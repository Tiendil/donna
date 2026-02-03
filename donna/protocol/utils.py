import sys

from donna.protocol.cells import Cell
from donna.protocol.modes import get_cell_formatter


def instant_output(cells: list[Cell]) -> None:
    if not cells:
        return

    formatter = get_cell_formatter()

    formatted_cells: list[bytes] = []
    for cell in cells:
        # TODO: we should refactor that hardcoded check somehow
        if cell.kind == "donna_log":
            formatted_cells.append(formatter.format_log(cell, single_mode=True))
        else:
            formatted_cells.append(formatter.format_cell(cell, single_mode=False))

    sys.stdout.buffer.write(b"\n\n".join(formatted_cells) + b"\n\n")
    sys.stdout.buffer.flush()
