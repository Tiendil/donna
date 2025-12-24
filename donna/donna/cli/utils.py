from collections.abc import Iterable

import typer

from donna.agents.domain import AgentCellHistory


def output_cells(cells: Iterable[AgentCellHistory]) -> None:
    for cell in cells:
        typer.echo(cell.body)
