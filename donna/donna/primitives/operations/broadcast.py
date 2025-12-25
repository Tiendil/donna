import importlib.util
import pathlib
from typing import TYPE_CHECKING, Iterable, Iterator

from donna.machine.action_requests import ActionRequest
from donna.machine.cells import WorkflowCell
from donna.core.entities import BaseEntity
from donna.world.layout import layout
from donna.domain.types import EventId, OperationId, OperationResultId
from donna.machine.events import Event, EventTemplate
from donna.machine.tasks import Task, TaskState, WorkUnit
from donna.machine.operations import Operation

if TYPE_CHECKING:
    from donna.machine.changes import Change


class Broadcast(Operation):
    def execute(self, task: Task, unit: WorkUnit) -> Iterator["Change"]:
        from donna.machine.changes import ChangeEvent

        for result in self.results:
            yield ChangeEvent(Event.build(result.event_id, self.id, task.id))
