from collections.abc import Iterable

from llm_tool_cli.core.result import Ok, Result
from llm_tool_cli.protocol.logic_cells.base import LogicCell

from donna.protocol.journal import JournalRecord


class FakeOutputEmitter:
    def __init__(self) -> None:
        self.cells: list[LogicCell] = []
        self.journal_records: list[JournalRecord] = []

    def emit_cells(self, cells: Iterable[LogicCell]) -> None:
        self.cells.extend(cells)

    def emit_journal(self, record: JournalRecord) -> None:
        self.journal_records.append(record)


class FakeJournal:
    def __init__(self) -> None:
        self.messages: list[tuple[str | None, str]] = []
        self.records: list[dict[str, object]] = []

    def add(self, message: str, actor_id: str | None = None) -> Result[object]:
        self.messages.append((actor_id, message))
        self.records.append({"message": message, "actor_id": actor_id})
        return Ok(None)
