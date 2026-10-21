from collections.abc import Iterator
from contextlib import contextmanager

from llm_tool_cli.config.runtime import RuntimeConfig, runtime_config
from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Err, Ok, Result
from llm_tool_cli.output import output
from llm_tool_cli.protocol import Protocol

from donna.context.tests.helpers import FakeOutputEmitter
from donna.domain.artifact_ids import ArtifactId
from donna.domain.python_path import PythonPath
from donna.machine import ArtifactRenderContext, Caches
from donna.machine.artifacts import Artifact
from donna.machine.caches import caches
from donna.machine.context import ExecutionContext, execution_context
from donna.machine.primitives import Primitive
from donna.machine.state import ConsistentState, MutableState
from donna.machine.tasks import Task, WorkUnit
from donna.runtime.tests.make import FakeStateStore


class FakeArtifacts:
    def __init__(self, artifact: Artifact | None = None, error: EnvironmentErrors | None = None) -> None:
        self.artifact = artifact
        self.error = error
        self.viewed: list[ArtifactId] = []
        self.executed: list[tuple[ArtifactId, Task, WorkUnit]] = []

    def load_for_view(self, artifact_id: ArtifactId) -> Result[Artifact]:
        self.viewed.append(artifact_id)
        if self.error is not None:
            return Err(self.error)
        assert self.artifact is not None
        return Ok(self.artifact)

    def load(self, artifact_id: ArtifactId, render_context: ArtifactRenderContext) -> Result[Artifact]:
        return self.load_for_view(artifact_id)

    def list(self, render_context: ArtifactRenderContext) -> Result[list[Artifact]]:
        if self.error is not None:
            return Err(self.error)
        assert self.artifact is not None
        return Ok([self.artifact])

    def load_for_execution(
        self,
        artifact_id: ArtifactId,
        task: Task,
        work_unit: WorkUnit,
    ) -> Result[Artifact]:
        self.executed.append((artifact_id, task, work_unit))
        if self.error is not None:
            return Err(self.error)
        assert self.artifact is not None
        return Ok(self.artifact)


class FakePrimitives:
    def __init__(self, primitive: Primitive | None = None, error: EnvironmentErrors | None = None) -> None:
        self.primitive = primitive
        self.error = error
        self.resolved: list[PythonPath] = []

    def resolve(self, primitive_id: PythonPath) -> Result[Primitive]:
        self.resolved.append(primitive_id)
        if self.error is not None:
            return Err(self.error)
        assert self.primitive is not None
        return Ok(self.primitive)


class MachineServices:
    def __init__(
        self,
        *,
        artifact: Artifact | None = None,
        primitive: Primitive | None = None,
        artifact_error: EnvironmentErrors | None = None,
        primitive_error: EnvironmentErrors | None = None,
        state: ConsistentState | None = None,
    ) -> None:
        self.artifacts = FakeArtifacts(artifact=artifact, error=artifact_error)
        self.primitives = FakePrimitives(primitive=primitive, error=primitive_error)
        self.caches = Caches(
            artifacts=self.artifacts,
            primitives=self.primitives,
            state=FakeStateStore(state=state if state is not None else MutableState.build().freeze()),
        )
        self.output = FakeOutputEmitter()


@contextmanager
def services_scope(value: MachineServices) -> Iterator[None]:
    with (
        caches.scope(value.caches),
        output.scope(value.output),
        execution_context.scope(ExecutionContext()),
        runtime_config.scope(RuntimeConfig(protocol=Protocol.human)),
    ):
        yield
