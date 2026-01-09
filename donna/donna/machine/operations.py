from typing import TYPE_CHECKING, Iterable

from donna.core.entities import BaseEntity
from donna.domain.ids import FullArtifactId, FullArtifactLocalId, OperationId
from donna.domain.types import OperationResultId, Slug
from donna.machine.cells import Cell
from donna.machine.tasks import Task, WorkUnit
from donna.world.markdown import SectionSource

if TYPE_CHECKING:
    from donna.machine.changes import Change


class OperationResult(BaseEntity):
    id: OperationResultId
    description: str
    next_operation_id: OperationId | None = None

    @classmethod
    def completed(cls, operation_id: OperationId) -> "OperationResult":
        return cls(
            id=OperationResultId(Slug("completed")),
            description="The operation was completed successfully.",
            next_operation_id=operation_id,
        )

    @classmethod
    def repeat(cls, operation_id: OperationId) -> "OperationResult":
        return cls(
            id=OperationResultId(Slug("repeat")),
            description="The operation needs to be repeated.",
            next_operation_id=operation_id,
        )

    def cells(self) -> list[Cell]:
        return [
            Cell.build_meta(
                kind="operation_result",
                result_description=self.description,
                result_id=self.id,
                next_operation_id=self.next_operation_id,
            )
        ]


class OperationKind(BaseEntity):
    id: str
    title: str
    operation: type["Operation"]

    def execute(self, task: Task, unit: WorkUnit, operation: "Operation") -> Iterable["Change"]:
        raise NotImplementedError("You MUST implement this method.")

    def construct(self, artifact_id: FullArtifactId, section: SectionSource) -> "Operation":  # type: ignore[override]
        raise NotImplementedError("You MUST implement this method.")

    def cells(self) -> list[Cell]:
        return [Cell.build_meta(kind="operation_kind", id=self.id, title=self.title)]


class Operation(BaseEntity):
    id: OperationId
    artifact_id: FullArtifactId

    kind: str
    title: str

    results: list[OperationResult]

    @property
    def full_id(self) -> FullArtifactLocalId:
        return self.artifact_id.to_full_local(self.id)

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
