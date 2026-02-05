import functools
import sys
from collections.abc import Iterable
from typing import Callable, ParamSpec

import pathlib
import typer
import click

from donna.core.errors import EnvironmentError
from donna.core.result import UnwrapError
from donna.protocol.cells import Cell
from donna.protocol.modes import get_cell_formatter
from donna.workspaces.initialization import initialize_runtime


def output_cells(cells: Iterable[Cell]) -> None:
    formatter = get_cell_formatter()

    output = formatter.format_cells(list(cells))

    sys.stdout.buffer.write(output)


P = ParamSpec("P")


def cells_cli(func: Callable[P, Iterable[Cell]]) -> Callable[P, None]:

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
        try:
            cells = func(*args, **kwargs)
        except UnwrapError as e:
            if isinstance(e.arguments["error"], EnvironmentError):
                cells = [e.arguments["error"].node().info()]
            elif isinstance(e.arguments["error"], Iterable):
                cells = [error.node().info() for error in e.arguments["error"] if isinstance(error, EnvironmentError)]
            else:
                raise

        output_cells(cells)

    return wrapper


def root_dir_from_context() -> pathlib.Path | None:
    try:
        ctx = click.get_current_context()
    except RuntimeError:
        return None

    if ctx is None or ctx.obj is None:
        return None

    root_dir = ctx.obj.get("root_dir")
    if isinstance(root_dir, pathlib.Path):
        return root_dir

    return None


def try_initialize_donna() -> None:
    root_dir = root_dir_from_context()
    result = initialize_runtime(root_dir=root_dir)

    if result.is_ok():
        return

    output_cells([error.node().info() for error in result.unwrap_err()])

    raise typer.Exit(code=0)
