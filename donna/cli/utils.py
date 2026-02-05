import functools
import pathlib
import sys
from collections.abc import Iterable
from typing import Callable, ParamSpec

import typer

from donna.core import errors as core_errors
from donna.core.errors import EnvironmentError
from donna.core.result import UnwrapError
from donna.protocol.cells import Cell
from donna.protocol.modes import Mode, get_cell_formatter
from donna.workspaces import config as workspace_config
from donna.workspaces import errors as workspace_errors
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


def _is_workspace_init_command() -> bool:
    args = sys.argv[1:]
    if "workspaces" not in args:
        return False

    index = args.index("workspaces")
    return len(args) > index + 1 and args[index + 1] == "init"


def try_initialize_donna(project_dir: pathlib.Path | None, protocol: Mode) -> None:
    if _is_workspace_init_command():
        return

    workspace_config.set_mode(protocol)
    result = initialize_runtime(root_dir=project_dir)

    if result.is_ok():
        return

    errors = result.unwrap_err()

    output_cells([error.node().info() for error in errors])

    raise typer.Exit(code=0)
