import enum
from collections.abc import Mapping
from typing import TYPE_CHECKING

from donna.domain.ids import SectionId
from donna.machine.artifacts import ArtifactSectionConfig, ArtifactSectionMeta
from donna.machine.primitives import Primitive
from donna.protocol.cells import MetaValue

if TYPE_CHECKING:
    pass


class FsmMode(enum.Enum):
    start = "start"
    normal = "normal"
    final = "final"


class OperationKind(Primitive):
    pass


class OperationConfig(ArtifactSectionConfig):
    fsm_mode: FsmMode = FsmMode.normal


class OperationMeta(ArtifactSectionMeta):
    fsm_mode: FsmMode = FsmMode.normal
    allowed_transitions: set[SectionId]

    def cells_meta(self) -> Mapping[str, MetaValue]:
        return {"fsm_mode": self.fsm_mode.value, "allowed_transitions": [str(t) for t in self.allowed_transitions]}
