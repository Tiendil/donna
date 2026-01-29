import functools
import sys
from collections.abc import Iterable
from typing import Callable, ParamSpec

import typer

from donna.protocol.cells import Cell
from donna.protocol.modes import get_cell_formatter
from donna.world.initialization import initialize_environment


def output_cells(cells: Iterable[Cell]) -> None:
    formatter = get_cell_formatter()

    output = formatter.format_cells(list(cells))

    sys.stdout.buffer.write(output)


P = ParamSpec("P")


def cells_cli(func: Callable[P, Iterable[Cell]]) -> Callable[P, None]:

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
        cells = func(*args, **kwargs)
        output_cells(cells)

    return wrapper


def try_initialize_donna() -> None:
    result = initialize_environment()

    if result.is_ok():
        return

    output_cells([error.node().info() for error in result.unwrap_err()])

    raise typer.Exit(code=0)
