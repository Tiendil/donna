import sys

from donna.machine.journal import JournalRecord
from donna.protocol.cells import Cell
from donna.protocol.modes import get_cell_formatter


def instant_output(text: bytes) -> None:
    sys.stdout.buffer.write(text + b"\n")
    sys.stdout.buffer.flush()


def instant_output_journal(record: JournalRecord) -> None:
    formatter = get_cell_formatter()
    formatted_output = formatter.format_journal(record)
    instant_output(formatted_output)


def instant_output_cell(cell: Cell) -> None:
    formatter = get_cell_formatter()
    formatted_output = formatter.format_cell(cell, single_mode=False)
    instant_output(formatted_output)
