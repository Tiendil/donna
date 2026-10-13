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
from donna.machine import ArtifactRenderContext, Caches, ExecutionContext
from donna.machine.artifacts import Artifact
from donna.machine.caches import caches
from donna.machine.context import execution_context
from donna.machine.primitives import Primitive
from donna.machine.state import ConsistentState
from donna.machine.tasks import Task, WorkUnit


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

    def list(self, render_context: ArtifactRenderContext) -> Result[list[Artifact]]:
        return Ok([self.artifact])

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


class RuntimeServices:
    def __init__(self, *, state: ConsistentState | None, artifact: Artifact, primitive: Primitive) -> None:
        self.state = FakeStateStore(state=state)
        self.artifacts = FakeArtifacts(artifact)
        self.primitives = FakePrimitives(primitive)
        self.caches = Caches(artifacts=self.artifacts, primitives=self.primitives, state=self.state)
        self.output = FakeOutputEmitter()


@contextmanager
def services_scope(services: RuntimeServices) -> Iterator[RuntimeServices]:
    with (
        runtime_config.scope(RuntimeConfig(protocol=Protocol.human)),
        output.scope(services.output),
        caches.scope(services.caches),
        execution_context.scope(ExecutionContext()),
    ):
        yield services
