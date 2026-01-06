from typing import TYPE_CHECKING, Callable, Iterable

from donna.core.entities import BaseEntity
from donna.domain.types import OperationId, OperationResultId, Slug
from donna.machine.tasks import Task, WorkUnit

if TYPE_CHECKING:
    from donna.machine.changes import Change


class OperationResult(BaseEntity):
    id: OperationResultId
    description: str
    operation_id_: OperationId | Callable[[], OperationId]

    @property
    def operation_id(self) -> OperationId:
        if isinstance(self.operation_id_, str):
            return self.operation_id_

        return self.operation_id_()

    @classmethod
    def completed(cls, operation_id: OperationId | Callable[[], OperationId]) -> "OperationResult":
        return cls(
            id=OperationResultId(Slug("completed")),
            description="The operation was completed successfully.",
            operation_id_=operation_id,
        )

    @classmethod
    def repeat(cls, operation_id: OperationId | Callable[[], OperationId]) -> "OperationResult":
        return cls(
            id=OperationResultId(Slug("next_iteration")),
            description="The operation needs to be repeated.",
            operation_id_=operation_id,
        )


class Operation(BaseEntity):
    id: OperationId

    results: list[OperationResult]

    def execute(self, task: Task, unit: WorkUnit) -> Iterable["Change"]:
        raise NotImplementedError("You MUST implement this method.")

    def result(self, id: OperationResultId) -> OperationResult:
        for result in self.results:
            if result.id == id:
                return result

        raise NotImplementedError(f"OperationResult with id '{id}' does not exist")
