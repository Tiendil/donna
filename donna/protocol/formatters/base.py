from abc import ABC, abstractmethod

from donna.machine.journal import JournalRecord
from donna.protocol.cells import Cell


class Formatter(ABC):

    @abstractmethod
    def format_cell(self, cell: Cell) -> bytes: ...  # noqa: E704

    @abstractmethod
    def format_journal(self, record: JournalRecord) -> bytes: ...  # noqa: E704
