import contextvars
from contextlib import ExitStack
from typing import cast

from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Err, Ok, Result

from donna.context.context import Context
from donna.context.context import reset_context as reset_runtime_context
from donna.context.context import set_context as set_runtime_context
from donna.context.tests.helpers import FakeJournal, FakeOutputEmitter
from donna.domain.artifact_ids import ArtifactId
from donna.domain.python_path import PythonPath
from donna.machine import ExecutionContext
from donna.machine.artifacts import Artifact
from donna.machine.context import MachineContext, execution_context
from donna.machine.context import reset_context as reset_machine_context
from donna.machine.context import set_context as set_machine_context
from donna.machine.primitives import Primitive
from donna.machine.state import ConsistentState
from donna.machine.tasks import Task, WorkUnit
from donna.workspaces.artifacts import ArtifactRenderContext


class FakeStateStore:
    def __init__(self, state: ConsistentState | None = None, errors: EnvironmentErrors | None = None) -> None:
        self.state = state
        self.errors = errors
        self.loaded_count = 0
        self.saved: list[ConsistentState] = []

    def load(self) -> Result[ConsistentState]:
        self.loaded_count += 1

        if self.errors is not None:
            return Err(self.errors)

        assert self.state is not None
        return Ok(self.state)

    def save(self, state: ConsistentState) -> Result[None]:
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

    def load(self, artifact_id: ArtifactId, render_context: ArtifactRenderContext) -> Result[Artifact]:
        self.loaded.append((artifact_id, render_context))
        return Ok(self.artifact)

    def load_for_view(self, artifact_id: ArtifactId) -> Result[Artifact]:
        self.viewed.append(artifact_id)
        return Ok(self.artifact)

    def load_for_execution(
        self,
        artifact_id: ArtifactId,
        task: Task,
        work_unit: WorkUnit,
    ) -> Result[Artifact]:
        self.executed.append((artifact_id, task, work_unit))
        return Ok(self.artifact)


class FakePrimitives:
    def __init__(self, primitive: Primitive) -> None:
        self.primitive = primitive
        self.resolved: list[PythonPath] = []

    def resolve(self, primitive_id: PythonPath) -> Result[Primitive]:
        self.resolved.append(primitive_id)
        return Ok(self.primitive)


class FakeRuntimeContext:
    def __init__(self, *, state: ConsistentState | None, artifact: Artifact, primitive: Primitive) -> None:
        self.state = FakeStateStore(state=state)
        self.artifacts = FakeArtifacts(artifact)
        self.primitives = FakePrimitives(primitive)
        self.journal = FakeJournal()
        self.output = FakeOutputEmitter()


class InstalledContext:
    def __init__(self, context: FakeRuntimeContext) -> None:
        self.context = context
        self._runtime_token: contextvars.Token[Context | None] | None = None
        self._machine_token: contextvars.Token[MachineContext | None] | None = None
        self._resources = ExitStack()

    def __enter__(self) -> FakeRuntimeContext:
        self._resources.enter_context(execution_context.scope(ExecutionContext()))
        self._runtime_token = set_runtime_context(cast(Context, self.context))
        self._machine_token = set_machine_context(self.context)
        return self.context

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        assert self._machine_token is not None
        assert self._runtime_token is not None
        reset_machine_context(self._machine_token)
        reset_runtime_context(self._runtime_token)
        self._resources.close()


def installed_context(context: FakeRuntimeContext) -> InstalledContext:
    return InstalledContext(context)
