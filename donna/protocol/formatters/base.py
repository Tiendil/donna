from abc import ABC, abstractmethod

from donna.protocol.cells import Cell
from donna.protocol.journal import JournalRecord


class Formatter(ABC):

    @abstractmethod
    def format_cell(self, cell: Cell) -> bytes: ...  # noqa: E704

    @abstractmethod
    def format_journal(self, record: JournalRecord) -> bytes: ...  # noqa: E704
