import enum
from typing import TYPE_CHECKING

from donna.domain.ids import SectionId
from donna.machine.artifacts import ArtifactSectionConfig, ArtifactSectionMeta
from donna.machine.primitives import Primitive

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
