import sys
from collections.abc import Iterable

import typer

from donna.cli.application import app
from donna.cli.utils import cells_cli, output_cells
from donna.machine import journal as machine_journal
from donna.machine.sessions import load_state
from donna.protocol.cell_shortcuts import operation_succeeded
from donna.protocol.cells import Cell
from donna.protocol.modes import get_cell_formatter

journal_cli = typer.Typer()


@journal_cli.command(help="Append a new journal record.")
@cells_cli
def write(
    actor_id: str = typer.Argument(..., help="Actor identifier (for example: 'agent_123' or 'donna')."),
    message: str = typer.Argument(..., help="Single-line message to append to journal (newlines are not allowed)."),
) -> Iterable[Cell]:
    state = load_state().unwrap()

    machine_journal.add(
        actor_id=actor_id,
        message=message,
        current_task_id=str(state.current_task.id) if state.current_task else None,
        current_work_unit_id=None,
        current_operation_id=None,
    ).unwrap()
    return [operation_succeeded("Journal record appended.")]


@journal_cli.command(help="View journal records.")
def view(  # noqa: CCR001
    lines: int | None = typer.Option(None, min=1, help="Show only the last N records."),
    follow: bool = typer.Option(False, help="Keep printing records as they are appended."),
) -> None:
    iterator = machine_journal.read(lines=lines, follow=follow)

    formatter = get_cell_formatter()

    for record_result in iterator:
        if record_result.is_err():
            output_cells([error.node().info() for error in record_result.unwrap_err()])
            return

        record = record_result.unwrap()
        rendered = formatter.format_journal(record)
        sys.stdout.buffer.write(rendered + b"\n")
        sys.stdout.buffer.flush()


app.add_typer(
    journal_cli,
    name="journal",
    help="Append and inspect session actions journal records.",
)
