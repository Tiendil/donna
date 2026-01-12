import enum
from typing import TYPE_CHECKING, Iterable

from donna.core.entities import BaseEntity
from donna.domain.ids import FullArtifactId, FullArtifactLocalId, OperationId, OperationKindId
from donna.machine.cells import Cell
from donna.machine.tasks import Task, WorkUnit
from donna.world.markdown import SectionSource

if TYPE_CHECKING:
    from donna.machine.changes import Change


class OperationKind(BaseEntity):
    id: OperationKindId
    title: str
    operation: type["Operation"]

    def execute(self, task: Task, unit: WorkUnit, operation: "Operation") -> Iterable["Change"]:
        raise NotImplementedError("You MUST implement this method.")

    def construct(self, artifact_id: FullArtifactId, section: SectionSource) -> "Operation":  # type: ignore[override]
        raise NotImplementedError("You MUST implement this method.")

    def cells(self) -> list[Cell]:
        return [Cell.build_meta(kind="operation_kind", id=self.id, title=self.title)]


class OperationMode(enum.Enum):
    normal = "normal"
    final = "final"


class OperationConfig(BaseEntity):
    id: OperationId
    kind: OperationKindId
    mode: OperationMode = OperationMode.normal


class Operation(BaseEntity):
    id: OperationId
    artifact_id: FullArtifactId

    kind: OperationKindId
    title: str

    mode: OperationMode

    allowed_transtions: set[FullArtifactLocalId]

    @property
    def full_id(self) -> FullArtifactLocalId:
        return self.artifact_id.to_full_local(self.id)

    def cells(self) -> list[Cell]:
        return [Cell.build_meta(kind="operation", operation_id=str(self.id))]
