from typing import Protocol

from llm_tool_cli.core.context import ContextValue
from llm_tool_cli.core.result import Result


class MachineJournal(Protocol):
    def add(self, message: str, actor_id: str | None = None) -> Result[object]:
        pass


journal = ContextValue[MachineJournal]("donna_journal")
