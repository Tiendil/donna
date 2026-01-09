from typing import TYPE_CHECKING, Callable, Iterable

from donna.core.entities import BaseEntity
from donna.domain.types import OperationId, OperationResultId, Slug
from donna.machine.cells import Cell
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
            id=OperationResultId(Slug("repeat")),
            description="The operation needs to be repeated.",
            operation_id_=operation_id,
        )

    def cells(self) -> list[Cell]:
        return [
            Cell.build_meta(
                kind="operation_result",
                result_description=self.description,
                result_id=self.id,
                operation_id=self.operation_id,
            )
        ]


class OperationKind(BaseEntity):
    id: str
    title: str

    def execute(self, task: Task, unit: WorkUnit, operation: 'Operation') -> Iterable["Change"]:
        raise NotImplementedError("You MUST implement this method.")

    def cells(self) -> list[Cell]:
        return [
            Cell.build_meta(
                kind="operation_kind",
                id=self.id,
                title=self.title
            )
        ]


class Operation(BaseEntity):
    id: OperationId
    title: str

    results: list[OperationResult]

    def result(self, id: OperationResultId) -> OperationResult:
        for result in self.results:
            if result.id == id:
                return result

        raise NotImplementedError(f"OperationResult with id '{id}' does not exist")

    def cells(self) -> list[Cell]:
        cells = [Cell.build_meta(kind="operation", operation_id=str(self.id))]

        for result in self.results:
            cells.extend(result.cells())

        return cells
