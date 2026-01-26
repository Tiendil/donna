import sys
from collections.abc import Iterable

from donna.protocol.cells import Cell
from donna.protocol.modes import get_cell_formatter


def output_cells(cells: Iterable[Cell]) -> None:
    formatter = get_cell_formatter()

    output = formatter.format_cells(list(cells))

    sys.stdout.buffer.write(output)
