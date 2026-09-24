from abc import ABC, abstractmethod

from llm_tool_cli.core.errors import EnvironmentError

from donna.protocol.cells import Cell
from donna.protocol.journal import JournalRecord


class Formatter(ABC):

    def format_error(self, error: EnvironmentError) -> bytes:
        return f"{error.format_message()}\n".encode()

    @abstractmethod
    def format_cell(self, cell: Cell) -> bytes: ...  # noqa: E704

    @abstractmethod
    def format_journal(self, record: JournalRecord) -> bytes: ...  # noqa: E704
