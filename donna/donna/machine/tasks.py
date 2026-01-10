import copy
import enum
from typing import TYPE_CHECKING, Any, cast

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.ids import FullArtifactLocalId, OperationId, next_id
from donna.domain.types import TaskId, WorkUnitId

if TYPE_CHECKING:
    from donna.machine.changes import Change


class TaskState(enum.StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    # Task should not have WAITING state,
    # because work unit may wait for input, not the whole task.
    # For example:
    # - a work unit requests agent work
    # - while agent processing units's request, it adds more work units
    # - donna may be able to process those units without waiting for the agent


class Task(BaseEntity):
    id: TaskId
    state: TaskState
    context: dict[str, Any]

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)

    @classmethod
    def build(cls) -> "Task":
        return Task(
            id=next_id(TaskId),
            state=TaskState.TODO,
            context={},
        )


class WorkUnitState(enum.StrEnum):
    TODO = "todo"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkUnit(BaseEntity):
    state: WorkUnitState
    id: WorkUnitId
    task_id: TaskId
    operation_id: FullArtifactLocalId
    context: dict[str, Any]

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)

    @classmethod
    def build(
        cls,
        task_id: TaskId,
        operation_id: FullArtifactLocalId,
        context: dict[str, Any] | None = None,
    ) -> "WorkUnit":

        id = next_id(WorkUnitId)

        if context is None:
            context = {}

        unit = cls(
            state=WorkUnitState.TODO,
            task_id=task_id,
            id=id,
            operation_id=operation_id,
            context=copy.deepcopy(context),
        )

        return unit

    def run(self, task: Task) -> list["Change"]:
        from donna.std.code.workflows import Workflow
        from donna.world import navigator
        from donna.world.primitives_register import register

        if self.state != WorkUnitState.TODO:
            raise NotImplementedError("Can only run a work unit in TODO state")

        workflow = cast(Workflow, navigator.load_artifact(self.operation_id.full_artifact_id))

        operation = workflow.get_operation(cast(OperationId, self.operation_id.local_id))

        if not operation:
            raise NotImplementedError(f"Operation with id '{self.operation_id.local_id}' not found")

        operation_kind = register().operations.get(operation.kind)
        assert operation_kind is not None

        cells = list(operation_kind.execute(task, self, operation))

        self.state = WorkUnitState.COMPLETED

        return cells
