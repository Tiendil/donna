import importlib.util
import pathlib
from typing import TYPE_CHECKING, Iterable, Iterator

from donna.machine.cells import WorkflowCell
from donna.machine.action_requests import ActionRequest
from donna.core.entities import BaseEntity
from donna.world.layout import layout
from donna.domain.types import EventId, OperationId, OperationResultId
from donna.machine.events import Event, EventTemplate
from donna.machine.tasks import Task, TaskState, WorkUnit

if TYPE_CHECKING:
    from donna.workflows.changes import Change


class OperationExport(BaseEntity):
    name: str
    description: str


class OperationResult(BaseEntity):
    id: OperationResultId
    description: str
    event_id: EventId

    @classmethod
    def completed(cls, event_id: EventId) -> "OperationResult":
        return cls(
            id=OperationResultId("completed"),
            description="The action was completed successfully.",
            event_id=event_id,
        )


class Operation(BaseEntity):
    id: OperationId

    trigger_on: list[EventTemplate]

    results: list[OperationResult]

    export: OperationExport | None = None

    def execute(self, task: Task, unit: WorkUnit) -> Iterable["Change"]:
        raise NotImplementedError("You MUST implement this method.")

    def result(self, id: OperationResultId) -> OperationResult:
        for result in self.results:
            if result.id == id:
                return result

        raise NotImplementedError(f"OperationResult with id '{id}' does not exist")

    def is_workflow(self) -> bool:
        return self.export is not None

    def workflow_cell(self) -> WorkflowCell:
        return WorkflowCell(
            story_id=None,
            task_id=None,
            work_unit_id=None,
            workflow_id=self.id,
            name=self.export.name,
            description=self.export.description,
        )
