from typing import Any

import jinja2
from jinja2.runtime import Context

from donna.domain.ids import (
    ArtifactKindId,
    FullArtifactId,
    FullArtifactLocalId,
    NamespaceId,
    OperationId,
    OperationKindId,
    RendererKindId,
)
from donna.machine.artifacts import Artifact, ArtifactInfo, ArtifactKind
from donna.machine.cells import Cell
from donna.machine.operations import OperationKind, OperationMode, OperationMeta, FsmMode
from donna.machine.templates import RendererKind
from donna.machine.artifacts import Artifact, ArtifactSection, ArtifactMeta
from donna.world.markdown import ArtifactSource, SectionSource
from donna.world.primitives_register import register
from donna.world.templates import RenderMode


class WorkflowMeta(ArtifactMeta):
    start_operation_id: FullArtifactLocalId

    def cells_meta(self) -> dict[str, Any]:
        return {"start_operation_id": str(self.start_operation_id)}
