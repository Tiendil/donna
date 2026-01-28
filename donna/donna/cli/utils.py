import sys
from collections.abc import Iterable

import typer

from donna.protocol.cells import Cell
from donna.protocol.modes import get_cell_formatter
from donna.world.initialization import initialize_environment


def output_cells(cells: Iterable[Cell]) -> None:
    formatter = get_cell_formatter()

    output = formatter.format_cells(list(cells))

    sys.stdout.buffer.write(output)


def try_initialize_donna() -> None:
    result = initialize_environment()

    if result.is_ok():
        return

    output_cells([error.node().info() for error in result.unwrap_err()])

    raise typer.Exit(code=0)
