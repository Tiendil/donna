from collections.abc import Iterable

import typer

from donna.machine.cells import Cell


def output_cells(cells: Iterable[Cell]) -> None:
    for cell in cells:
        typer.echo(cell.render())


def template_is_not_allowed(name: str, text: str) -> None:
    if '{' in text:
        raise NotImplementedError(f"This command does not support templates for '{name}', you passed the value '{text}'")
