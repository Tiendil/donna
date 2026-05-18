from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result
from donna.protocol.cells import Cell
from donna.protocol.journal import JournalRecord


class FakeOutputEmitter:
    def __init__(self) -> None:
        self.cells: list[Cell] = []
        self.journal_records: list[JournalRecord] = []

    def emit_cell(self, cell: Cell) -> None:
        self.cells.append(cell)

    def emit_journal(self, record: JournalRecord) -> None:
        self.journal_records.append(record)


class FakeJournal:
    def __init__(self) -> None:
        self.messages: list[tuple[str | None, str]] = []
        self.records: list[dict[str, object]] = []

    def add(self, message: str, actor_id: str | None = None) -> Result[object, ErrorsList]:
        self.messages.append((actor_id, message))
        self.records.append({"message": message, "actor_id": actor_id})
        return Ok(None)
