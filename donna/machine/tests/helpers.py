from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Err, Ok, Result

from donna.context.tests.helpers import FakeJournal
from donna.domain.artifact_ids import ArtifactId, ArtifactSectionId
from donna.domain.internal_ids import WorkUnitId
from donna.domain.python_path import PythonPath
from donna.machine.artifacts import Artifact
from donna.machine.context import ValueScope
from donna.machine.primitives import Primitive
from donna.machine.tasks import Task, WorkUnit


class FakeArtifacts:
    def __init__(self, artifact: Artifact | None = None, error: EnvironmentErrors | None = None) -> None:
        self.artifact = artifact
        self.error = error
        self.viewed: list[ArtifactId] = []
        self.executed: list[tuple[ArtifactId, Task, WorkUnit]] = []

    def load_for_view(self, artifact_id: ArtifactId) -> Result[Artifact, EnvironmentErrors]:
        self.viewed.append(artifact_id)
        if self.error is not None:
            return Err(self.error)
        assert self.artifact is not None
        return Ok(self.artifact)

    def load_for_execution(
        self,
        artifact_id: ArtifactId,
        task: Task,
        work_unit: WorkUnit,
    ) -> Result[Artifact, EnvironmentErrors]:
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

    def resolve(self, primitive_id: PythonPath) -> Result[Primitive, EnvironmentErrors]:
        self.resolved.append(primitive_id)
        if self.error is not None:
            return Err(self.error)
        assert self.primitive is not None
        return Ok(self.primitive)


class FakeMachineContext:
    def __init__(
        self,
        *,
        artifact: Artifact | None = None,
        primitive: Primitive | None = None,
        artifact_error: EnvironmentErrors | None = None,
        primitive_error: EnvironmentErrors | None = None,
    ) -> None:
        self._artifacts = FakeArtifacts(artifact=artifact, error=artifact_error)
        self._primitives = FakePrimitives(primitive=primitive, error=primitive_error)
        self._journal = FakeJournal()
        self._current_work_unit_id: ValueScope[WorkUnitId] = ValueScope()
        self._current_operation_id: ValueScope[ArtifactSectionId] = ValueScope()

    @property
    def artifacts(self) -> FakeArtifacts:
        return self._artifacts

    @property
    def primitives(self) -> FakePrimitives:
        return self._primitives

    @property
    def journal(self) -> FakeJournal:
        return self._journal

    @property
    def current_work_unit_id(self) -> ValueScope[WorkUnitId]:
        return self._current_work_unit_id

    @property
    def current_operation_id(self) -> ValueScope[ArtifactSectionId]:
        return self._current_operation_id
