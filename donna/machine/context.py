from __future__ import annotations

import contextvars
from typing import Protocol

from llm_tool_cli.core.context import ContextValue
from llm_tool_cli.core.entities import BaseEntity
from llm_tool_cli.core.result import Result

from donna.domain.artifact_ids import ArtifactSectionId
from donna.domain.internal_ids import WorkUnitId
from donna.machine import errors as machine_errors


class ExecutionContext(BaseEntity):
    current_work_unit_id: WorkUnitId | None = None
    current_operation_id: ArtifactSectionId | None = None


execution_context = ContextValue[ExecutionContext]("donna_execution_context")


class MachineJournal(Protocol):
    def add(self, message: str, actor_id: str | None = None) -> Result[object]:
        pass


class MachineContext(Protocol):
    @property
    def journal(self) -> MachineJournal:
        pass


_context_var: contextvars.ContextVar[MachineContext | None] = contextvars.ContextVar(
    "donna_machine_context",
    default=None,
)


def set_context(new_context: MachineContext) -> contextvars.Token[MachineContext | None]:
    return _context_var.set(new_context)


def reset_context(token: contextvars.Token[MachineContext | None]) -> None:
    _context_var.reset(token)


def context() -> MachineContext:
    current = _context_var.get()
    if current is None:
        raise machine_errors.MachineContextNotSet()

    return current
