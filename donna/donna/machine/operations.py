import enum
from typing import TYPE_CHECKING, Any

from donna.domain.ids import FullArtifactLocalId
from donna.machine.artifacts import ArtifactSectionConfig, ArtifactSectionKind, ArtifactSectionMeta
from donna.world.sources.markdown import MarkdownSectionMixin

if TYPE_CHECKING:
    pass


class FsmMode(enum.Enum):
    start = "start"
    normal = "normal"
    final = "final"


class OperationKind(MarkdownSectionMixin, ArtifactSectionKind):
    pass


class OperationConfig(ArtifactSectionConfig):
    fsm_mode: FsmMode = FsmMode.normal


class OperationMeta(ArtifactSectionMeta):
    fsm_mode: FsmMode = FsmMode.normal
    allowed_transtions: set[FullArtifactLocalId]

    def cells_meta(self) -> dict[str, Any]:
        return {"fsm_mode": self.fsm_mode.value, "allowed_transtions": [str(t) for t in self.allowed_transtions]}
