from __future__ import annotations

import contextvars
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar

from donna.core.errors import ErrorsList
from donna.core.result import Result
from donna.domain.artifact_ids import ArtifactId, ArtifactSectionId
from donna.domain.internal_ids import WorkUnitId
from donna.domain.python_path import PythonPath
from donna.machine import errors as machine_errors

if TYPE_CHECKING:
    from donna.machine.artifacts import Artifact
    from donna.machine.primitives import Primitive
    from donna.machine.tasks import Task, WorkUnit

TScopedValue = TypeVar("TScopedValue")


class ValueScope(Generic[TScopedValue]):
    __slots__ = ("_value",)

    def __init__(self, initial: TScopedValue | None = None) -> None:
        self._value: TScopedValue | None = initial

    def get(self) -> TScopedValue | None:
        return self._value

    @contextmanager
    def scope(self, value: TScopedValue | None) -> Iterator[None]:
        previous = self._value
        self._value = value
        try:
            yield
        finally:
            self._value = previous


class MachineArtifacts(Protocol):
    def load_for_view(self, artifact_id: ArtifactId) -> Result["Artifact", ErrorsList]:
        pass

    def load_for_execution(
        self,
        artifact_id: ArtifactId,
        task: "Task",
        work_unit: "WorkUnit",
    ) -> Result["Artifact", ErrorsList]:
        pass


class MachinePrimitives(Protocol):
    def resolve(self, primitive_id: PythonPath) -> Result["Primitive", ErrorsList]:
        pass


class MachineJournal(Protocol):
    def add(self, message: str, actor_id: str | None = None) -> Result[Any, ErrorsList]:
        pass


class MachineContext(Protocol):
    @property
    def artifacts(self) -> MachineArtifacts:
        pass

    @property
    def primitives(self) -> MachinePrimitives:
        pass

    @property
    def journal(self) -> MachineJournal:
        pass

    @property
    def current_work_unit_id(self) -> ValueScope[WorkUnitId]:
        pass

    @property
    def current_operation_id(self) -> ValueScope[ArtifactSectionId]:
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
