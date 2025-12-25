import copy
import enum
from typing import TYPE_CHECKING, Any

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.types import OperationId, StoryId, TaskId, WorkUnitId, new_task_id, new_work_unit_id

if TYPE_CHECKING:
    from donna.workflows.changes import Change


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
    story_id: StoryId
    context: dict[str, Any]

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)

    @classmethod
    def build(cls, story_id: StoryId) -> "Task":
        return Task(
            id=new_task_id(),
            state=TaskState.TODO,
            story_id=story_id,
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
    operation: OperationId
    context: dict[str, Any]

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)

    @classmethod
    def build(
        cls,
        task_id: TaskId,
        operation: OperationId,
        context: dict[str, Any] | None = None,
    ) -> "WorkUnit":

        id = new_work_unit_id()

        if context is None:
            context = {}

        unit = cls(
            state=WorkUnitState.TODO,
            task_id=task_id,
            id=id,
            operation=operation,
            context=copy.deepcopy(context),
        )

        return unit

    def run(self, task: Task) -> list["Change"]:
        from donna.workflows.operations import storage

        if self.state != WorkUnitState.TODO:
            raise NotImplementedError("Can only run a work unit in TODO state")

        operation = storage().get(self.operation)

        if not operation:
            raise NotImplementedError(f"Operation with kind '{self.operation}' not found")

        cells = list(operation.execute(task, self))

        self.state = WorkUnitState.COMPLETED

        return cells
