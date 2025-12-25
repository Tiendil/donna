import importlib.util
import pathlib
from typing import TYPE_CHECKING, Iterable, Iterator

from donna.agents.domain import ActionRequest, WorkflowCell
from donna.core.entities import BaseEntity
from donna.domain.layout import layout
from donna.domain.types import EventId, OperationId, OperationResultId
from donna.stories.events import Event, EventTemplate
from donna.workflows.tasks import Task, TaskState, WorkUnit
from donna.machine import Operation

if TYPE_CHECKING:
    from donna.workflows.changes import Change


class Finish(Operation):
    def execute(self, task: Task, unit: WorkUnit) -> Iterator["Change"]:
        from donna.workflows.changes import ChangeTaskState

        yield ChangeTaskState(TaskState.COMPLETED)
