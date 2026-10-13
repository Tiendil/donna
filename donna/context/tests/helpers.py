from llm_tool_cli.core.result import Ok, Result
from llm_tool_cli.protocol.logic_cells.base import LogicCell

from donna.protocol.journal import JournalCell


class FakeOutputEmitter:
    def __init__(self) -> None:
        self.cells: list[LogicCell] = []
        self.journal_records: list[JournalCell] = []

    def emit(self, cells: list[LogicCell]) -> Result[None]:
        for cell in cells:
            if isinstance(cell, JournalCell):
                self.journal_records.append(cell)
            else:
                self.cells.append(cell)
        return Ok(None)

    def flush(self) -> None:
        pass

    def discard(self) -> None:
        self.cells = [cell for cell in self.cells if cell.is_warning]
