import copy
from typing import TYPE_CHECKING, Any, cast

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.ids import FullArtifactLocalId, OperationId, TaskId, WorkUnitId

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
    operation_id: FullArtifactLocalId
    context: dict[str, Any]

    @classmethod
    def build(
        cls,
        id: WorkUnitId,
        task_id: TaskId,
        operation_id: FullArtifactLocalId,
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

    def run(self, task: Task) -> list["Change"]:
        from donna.world import artifacts
        from donna.world.primitives_register import register

        workflow = artifacts.load_artifact(self.operation_id.full_artifact_id)

        operation = workflow.get_section(self.operation_id)

        if not operation:
            raise NotImplementedError(f"Operation with id '{self.operation_id.local_id}' not found")

        assert operation.kind is not None

        operation_kind = register().operations.get(operation.kind)

        assert operation_kind is not None

        cells = list(operation_kind.execute(task, self, operation))

        return cells
