import functools
import pathlib
import sys
from collections.abc import Iterable
from typing import Callable, ParamSpec

import typer

from donna.core.errors import EnvironmentError, ErrorsList
from donna.core.result import UnwrapError
from donna.protocol.cells import Cell
from donna.protocol.modes import Mode, get_cell_formatter
from donna.workspaces import config as workspace_config
from donna.workspaces.initialization import initialize_runtime


def output_cells(cells: Iterable[Cell]) -> None:
    formatter = get_cell_formatter()

    for cell in cells:
        output = formatter.format_cell(cell)
        sys.stdout.buffer.write(output)


P = ParamSpec("P")


def _write_errors_to_journal(errors: ErrorsList) -> None:
    from donna.machine import journal as machine_journal

    for error in errors:
        message = f"Error: {error.node().journal_message()} [{error.code}]"

        machine_journal.add(
            message=message,
            actor_id="donna",
        )


def cells_cli(func: Callable[P, Iterable[Cell]]) -> Callable[P, None]:  # noqa: CCR001

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:  # noqa: CCR001
        try:
            cells = func(*args, **kwargs)
        except UnwrapError as e:
            errors: ErrorsList
            if isinstance(e.arguments["error"], EnvironmentError):
                errors = [e.arguments["error"]]
            elif isinstance(e.arguments["error"], Iterable):
                errors = [error for error in e.arguments["error"] if isinstance(error, EnvironmentError)]
            else:
                raise

            _write_errors_to_journal(errors)
            cells = [error.node().info() for error in errors]

        output_cells(cells)

    return wrapper


def _is_workspace_init_command() -> bool:
    args = sys.argv[1:]
    if "workspaces" not in args:
        return False

    index = args.index("workspaces")
    return len(args) > index + 1 and args[index + 1] == "init"


def try_initialize_donna(project_dir: pathlib.Path | None, protocol: Mode) -> None:
    from donna.context import Context, set_context

    if _is_workspace_init_command():
        workspace_config.protocol.set(protocol)
        if project_dir is not None:
            workspace_config.project_dir.set(project_dir)
        return

    result = initialize_runtime(root_dir=project_dir, protocol=protocol)

    if result.is_ok():
        set_context(Context())
        return

    errors = result.unwrap_err()

    output_cells([error.node().info() for error in errors])

    raise typer.Exit(code=0)
