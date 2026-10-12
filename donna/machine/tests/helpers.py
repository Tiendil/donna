from collections.abc import Iterator
from contextlib import contextmanager

from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Err, Ok, Result

from donna.context.state import StateCache
from donna.context.tests.helpers import FakeJournal
from donna.domain.artifact_ids import ArtifactId
from donna.domain.python_path import PythonPath
from donna.machine import ArtifactRenderContext, Caches
from donna.machine.artifacts import Artifact
from donna.machine.caches import caches
from donna.machine.journal import journal
from donna.machine.primitives import Primitive
from donna.machine.tasks import Task, WorkUnit


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
    ) -> None:
        self.artifacts = FakeArtifacts(artifact=artifact, error=artifact_error)
        self.primitives = FakePrimitives(primitive=primitive, error=primitive_error)
        self.caches = Caches(artifacts=self.artifacts, primitives=self.primitives, state=StateCache())
        self.journal = FakeJournal()


@contextmanager
def services_scope(value: MachineServices) -> Iterator[None]:
    with caches.scope(value.caches), journal.scope(value.journal):
        yield
