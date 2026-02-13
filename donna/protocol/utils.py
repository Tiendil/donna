import sys

from donna.machine.journal import JournalRecord
from donna.protocol.modes import get_cell_formatter


def instant_output(value: JournalRecord) -> None:
    formatter = get_cell_formatter()
    formatted_output = formatter.format_journal(value)
    sys.stdout.buffer.write(formatted_output + b"\n\n")
    sys.stdout.buffer.flush()
