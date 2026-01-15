from typing import Any

from donna.domain.ids import (
    FullArtifactLocalId,
)
from donna.machine.artifacts import ArtifactMeta


class WorkflowMeta(ArtifactMeta):
    start_operation_id: FullArtifactLocalId

    def cells_meta(self) -> dict[str, Any]:
        return {"start_operation_id": str(self.start_operation_id)}
