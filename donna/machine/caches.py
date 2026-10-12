from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from llm_tool_cli.core.context import ContextValue
from llm_tool_cli.core.result import Result

from donna.domain.artifact_ids import ArtifactId
from donna.domain.python_path import PythonPath

if TYPE_CHECKING:
    from donna.machine.artifacts import Artifact
    from donna.machine.primitives import Primitive
    from donna.machine.state import ConsistentState
    from donna.machine.tasks import Task, WorkUnit
    from donna.machine.templates import ArtifactRenderContext


class MachineArtifacts(Protocol):
    def load(self, artifact_id: ArtifactId, render_context: ArtifactRenderContext) -> Result[Artifact]:
        pass

    def list(self, render_context: ArtifactRenderContext) -> Result[list[Artifact]]:
        pass

    def load_for_view(self, artifact_id: ArtifactId) -> Result[Artifact]:
        pass

    def load_for_execution(self, artifact_id: ArtifactId, task: Task, work_unit: WorkUnit) -> Result[Artifact]:
        pass


class MachinePrimitives(Protocol):
    def resolve(self, primitive_id: PythonPath) -> Result[Primitive]:
        pass


class MachineState(Protocol):
    def load(self) -> Result[ConsistentState]:
        pass

    def save(self, state: ConsistentState) -> Result[None]:
        pass


class Caches:
    __slots__ = ("artifacts", "primitives", "state")

    def __init__(self, *, artifacts: MachineArtifacts, primitives: MachinePrimitives, state: MachineState) -> None:
        self.artifacts = artifacts
        self.primitives = primitives
        self.state = state


caches = ContextValue[Caches]("donna_caches")
