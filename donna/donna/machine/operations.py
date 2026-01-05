from typing import TYPE_CHECKING, Iterable

from donna.core.entities import BaseEntity
from donna.domain.types import EventId, OperationId, OperationResultId, Slug
from donna.machine.cells import Cell
from donna.machine.events import EventTemplate
from donna.machine.tasks import Task, WorkUnit

if TYPE_CHECKING:
    from donna.machine.changes import Change


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
            id=OperationResultId(Slug("completed")),
            description="The operation was completed successfully.",
            event_id=event_id,
        )

    @classmethod
    def next_iteration(cls, event_id: EventId) -> "OperationResult":
        return cls(
            id=OperationResultId(Slug("next_iteration")),
            description="The operation needs to be repeated.",
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

    def workflow_cell(self) -> Cell:
        assert self.export is not None

        return Cell.build_markdown(
            kind="workflow",
            content=self.export.description,
            workflow_id=self.id,
            workflow_name=self.export.name,
        )
