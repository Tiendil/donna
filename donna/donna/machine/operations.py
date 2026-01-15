import enum
from typing import TYPE_CHECKING, Iterable, Any

from donna.core.entities import BaseEntity
from donna.domain.ids import FullArtifactId, FullArtifactLocalId, OperationId, OperationKindId, ArtifactSectionConfig, ArtifactSectionKindId
from donna.machine.cells import Cell
from donna.machine.tasks import Task, WorkUnit
from donna.world.markdown import SectionSource
from donna.machine.artifacts import ArtifactSectionMeta, ArtifactSection

if TYPE_CHECKING:
    from donna.machine.changes import Change


class OperationKind(BaseEntity):
    id: ArtifactSectionKindId
    title: str

    def execute(self, task: Task, unit: WorkUnit, operation: ArtifactSection) -> Iterable["Change"]:
        raise NotImplementedError("You MUST implement this method.")

    def construct(self, artifact_id: FullArtifactId, section: SectionSource) -> ArtifactSection:  # type: ignore[override]
        raise NotImplementedError("You MUST implement this method.")

    def cells(self) -> list[Cell]:
        return [Cell.build_meta(kind="operation_kind", id=self.id, title=self.title)]


class FsmMode(enum.Enum):
    start = "start"
    normal = "normal"
    final = "final"


class OperationConfig(ArtifactSectionConfig):
    fsm_mode: FsmMode = FsmMode.normal


class OperationMeta(ArtifactSectionMeta):
    fsm_mode: FsmMode = FsmMode.normal
    allowed_transtions: set[FullArtifactLocalId]

    def cells_meta(self) -> dict[str, Any]:
        return {"fsm_mode": self.fsm_mode.value,
                "allowed_transtions": [str(t) for t in self.allowed_transtions]}
