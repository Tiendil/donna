from collections.abc import Iterable
from typing import Protocol

from llm_tool_cli.protocol.logic_cells.base import LogicCell

from donna.protocol.journal import JournalRecord


class OutputEmitter(Protocol):
    def emit_cells(self, cells: Iterable[LogicCell]) -> None:
        pass

    def emit_journal(self, record: JournalRecord) -> None:
        pass


class NoopEmitter:
    __slots__ = ()

    def emit_cells(self, cells: Iterable[LogicCell]) -> None:
        pass

    def emit_journal(self, record: JournalRecord) -> None:
        pass
