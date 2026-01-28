import copy
from typing import TYPE_CHECKING, Any

import pydantic

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.domain.ids import FullArtifactSectionId, TaskId, WorkUnitId

if TYPE_CHECKING:
    from donna.machine.changes import Change


class Task(BaseEntity):
    id: TaskId
    context: dict[str, Any]

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)

    @classmethod
    def build(cls, id: TaskId) -> "Task":
        return Task(
            id=id,
            context={},
        )


class WorkUnit(BaseEntity):
    id: WorkUnitId
    task_id: TaskId
    operation_id: FullArtifactSectionId
    context: dict[str, Any]

    @classmethod
    def build(
        cls,
        id: WorkUnitId,
        task_id: TaskId,
        operation_id: FullArtifactSectionId,
        context: dict[str, Any] | None = None,
    ) -> "WorkUnit":

        if context is None:
            context = {}

        unit = cls(
            task_id=task_id,
            id=id,
            operation_id=operation_id,
            context=copy.deepcopy(context),
        )

        return unit

    def run(self, task: Task) -> Result[list["Change"], ErrorsList]:
        from donna.machine.primitives import resolve_primitive
        from donna.world import artifacts

        workflow_result = artifacts.load_artifact(self.operation_id.full_artifact_id)
        if workflow_result.is_err():
            return Err(workflow_result.unwrap_err())

        workflow = workflow_result.unwrap()

        operation = workflow.get_section(self.operation_id.local_id)

        if not operation:
            raise NotImplementedError(f"Operation with id '{self.operation_id.local_id}' not found")

        operation_kind = resolve_primitive(operation.kind)

        cells = list(operation_kind.execute_section(task, self, operation))

        return Ok(cells)
