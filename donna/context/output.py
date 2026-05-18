from typing import Protocol

from donna.protocol.cells import Cell
from donna.protocol.journal import JournalRecord


class OutputEmitter(Protocol):
    def emit_cell(self, cell: Cell) -> None:
        pass

    def emit_journal(self, record: JournalRecord) -> None:
        pass


class NoopEmitter:
    __slots__ = ()

    def emit_cell(self, cell: Cell) -> None:
        pass

    def emit_journal(self, record: JournalRecord) -> None:
        pass
