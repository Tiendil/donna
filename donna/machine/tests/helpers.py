from typing import Any

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.artifact_ids import ArtifactId
from donna.domain.python_path import PythonPath
from donna.machine.artifacts import Artifact
from donna.machine.context import ValueScope
from donna.machine.primitives import Primitive
from donna.machine.tasks import Task, WorkUnit


class FakeArtifacts:
    def __init__(self, artifact: Artifact | None = None, error: ErrorsList | None = None) -> None:
        self.artifact = artifact
        self.error = error
        self.viewed: list[ArtifactId] = []
        self.executed: list[tuple[ArtifactId, Task, WorkUnit]] = []

    def load_for_view(self, artifact_id: ArtifactId) -> Result[Artifact, ErrorsList]:
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
    ) -> Result[Artifact, ErrorsList]:
        self.executed.append((artifact_id, task, work_unit))
        if self.error is not None:
            return Err(self.error)
        assert self.artifact is not None
        return Ok(self.artifact)


class FakePrimitives:
    def __init__(self, primitive: Primitive | None = None, error: ErrorsList | None = None) -> None:
        self.primitive = primitive
        self.error = error
        self.resolved: list[PythonPath] = []

    def resolve(self, primitive_id: PythonPath) -> Result[Primitive, ErrorsList]:
        self.resolved.append(primitive_id)
        if self.error is not None:
            return Err(self.error)
        assert self.primitive is not None
        return Ok(self.primitive)


class FakeJournal:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def add(self, message: str, actor_id: str | None = None) -> Result[Any, ErrorsList]:
        self.records.append({"message": message, "actor_id": actor_id})
        return Ok(None)


class FakeMachineContext:
    def __init__(
        self,
        *,
        artifact: Artifact | None = None,
        primitive: Primitive | None = None,
        artifact_error: ErrorsList | None = None,
        primitive_error: ErrorsList | None = None,
    ) -> None:
        self._artifacts = FakeArtifacts(artifact=artifact, error=artifact_error)
        self._primitives = FakePrimitives(primitive=primitive, error=primitive_error)
        self._journal = FakeJournal()
        self._current_work_unit_id: ValueScope[Any] = ValueScope()
        self._current_operation_id: ValueScope[Any] = ValueScope()

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
    def current_work_unit_id(self) -> ValueScope[Any]:
        return self._current_work_unit_id

    @property
    def current_operation_id(self) -> ValueScope[Any]:
        return self._current_operation_id
