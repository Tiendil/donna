import enum
from typing import TYPE_CHECKING, Any, Iterable

from donna.core.entities import BaseEntity
from donna.domain.ids import ArtifactSectionKindId, FullArtifactId, FullArtifactLocalId
from donna.machine.artifacts import ArtifactSection, ArtifactSectionConfig, ArtifactSectionMeta, ArtifactSectionKind
from donna.machine.cells import Cell
from donna.machine.tasks import Task, WorkUnit
from donna.world.markdown import SectionSource

if TYPE_CHECKING:
    from donna.machine.changes import Change


class FsmMode(enum.Enum):
    start = "start"
    normal = "normal"
    final = "final"


class OperationKind(ArtifactSectionKind):
    pass


class OperationConfig(ArtifactSectionConfig):
    fsm_mode: FsmMode = FsmMode.normal


class OperationMeta(ArtifactSectionMeta):
    fsm_mode: FsmMode = FsmMode.normal
    allowed_transtions: set[FullArtifactLocalId]

    def cells_meta(self) -> dict[str, Any]:
        return {"fsm_mode": self.fsm_mode.value, "allowed_transtions": [str(t) for t in self.allowed_transtions]}
