from collections.abc import Iterable

import typer

from donna.protocol.cells import Cell


def output_cells(cells: Iterable[Cell]) -> None:
    for cell in cells:
        typer.echo(cell.render())
