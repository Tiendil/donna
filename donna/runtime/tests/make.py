import contextvars
from typing import cast

from donna.context.context import Context
from donna.context.context import reset_context as reset_runtime_context
from donna.context.context import set_context as set_runtime_context
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.artifact_ids import ArtifactId, ArtifactSectionId
from donna.domain.internal_ids import WorkUnitId
from donna.domain.python_path import PythonPath
from donna.machine.artifacts import Artifact
from donna.machine.context import MachineContext, ValueScope
from donna.machine.context import reset_context as reset_machine_context
from donna.machine.context import set_context as set_machine_context
from donna.machine.primitives import Primitive
from donna.machine.state import ConsistentState
from donna.machine.tasks import Task, WorkUnit
from donna.protocol.cells import Cell
from donna.workspaces.artifacts import ArtifactRenderContext


class FakeStateStore:
    def __init__(self, state: ConsistentState | None = None, errors: ErrorsList | None = None) -> None:
        self.state = state
        self.errors = errors
        self.loaded_count = 0
        self.saved: list[ConsistentState] = []

    def load(self) -> Result[ConsistentState, ErrorsList]:
        self.loaded_count += 1

        if self.errors is not None:
            return Err(self.errors)

        assert self.state is not None
        return Ok(self.state)

    def save(self, state: ConsistentState) -> Result[None, ErrorsList]:
        self.saved.append(state)
        self.state = state
        self.errors = None
        return Ok(None)


class FakeArtifacts:
    def __init__(self, artifact: Artifact) -> None:
        self.artifact = artifact
        self.loaded: list[tuple[ArtifactId, ArtifactRenderContext]] = []
        self.viewed: list[ArtifactId] = []
        self.executed: list[tuple[ArtifactId, Task, WorkUnit]] = []

    def load(self, artifact_id: ArtifactId, render_context: ArtifactRenderContext) -> Result[Artifact, ErrorsList]:
        self.loaded.append((artifact_id, render_context))
        return Ok(self.artifact)

    def load_for_view(self, artifact_id: ArtifactId) -> Result[Artifact, ErrorsList]:
        self.viewed.append(artifact_id)
        return Ok(self.artifact)

    def load_for_execution(
        self,
        artifact_id: ArtifactId,
        task: Task,
        work_unit: WorkUnit,
    ) -> Result[Artifact, ErrorsList]:
        self.executed.append((artifact_id, task, work_unit))
        return Ok(self.artifact)


class FakePrimitives:
    def __init__(self, primitive: Primitive) -> None:
        self.primitive = primitive
        self.resolved: list[PythonPath] = []

    def resolve(self, primitive_id: PythonPath) -> Result[Primitive, ErrorsList]:
        self.resolved.append(primitive_id)
        return Ok(self.primitive)


class FakeJournal:
    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []

    def add(self, message: str, actor_id: str | None = None) -> Result[object, ErrorsList]:
        self.records.append({"message": message, "actor_id": actor_id})
        return Ok(None)


class FakeOutputEmitter:
    def __init__(self) -> None:
        self.cells: list[Cell] = []

    def emit_cell(self, cell: Cell) -> None:
        self.cells.append(cell)

    def emit_journal(self, record: object) -> None:
        pass


class FakeRuntimeContext:
    def __init__(self, *, state: ConsistentState | None, artifact: Artifact, primitive: Primitive) -> None:
        self.state = FakeStateStore(state=state)
        self.artifacts = FakeArtifacts(artifact)
        self.primitives = FakePrimitives(primitive)
        self.journal = FakeJournal()
        self.output = FakeOutputEmitter()
        self.current_work_unit_id: ValueScope[WorkUnitId] = ValueScope()
        self.current_operation_id: ValueScope[ArtifactSectionId] = ValueScope()


class InstalledContext:
    def __init__(self, context: FakeRuntimeContext) -> None:
        self.context = context
        self._runtime_token: contextvars.Token[Context | None] | None = None
        self._machine_token: contextvars.Token[MachineContext | None] | None = None

    def __enter__(self) -> FakeRuntimeContext:
        self._runtime_token = set_runtime_context(cast(Context, self.context))
        self._machine_token = set_machine_context(self.context)
        return self.context

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        assert self._machine_token is not None
        assert self._runtime_token is not None
        reset_machine_context(self._machine_token)
        reset_runtime_context(self._runtime_token)


def installed_context(context: FakeRuntimeContext) -> InstalledContext:
    return InstalledContext(context)
