from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from donna.core.entities import BaseEntity
from donna.domain.ids import ActionRequestId, FullArtifactSectionId, TaskId, WorkUnitId
from donna.machine.action_requests import ActionRequest
from donna.machine.tasks import Task, WorkUnit

if TYPE_CHECKING:
    from donna.machine.state import MutableState


class Change(BaseEntity, ABC):
    @abstractmethod
    def apply_to(self, state: "MutableState") -> None: ...  # noqa: E704


class ChangeFinishTask(Change):
    task_id: TaskId

    def apply_to(self, state: "MutableState") -> None:
        state.finish_workflow(self.task_id)


class ChangeAddWorkUnit(Change):
    task_id: TaskId
    operation_id: FullArtifactSectionId

    def apply_to(self, state: "MutableState") -> None:
        work_unit = WorkUnit.build(id=state.next_work_unit_id(), task_id=self.task_id, operation_id=self.operation_id)
        state.add_work_unit(work_unit)


class ChangeAddTask(Change):
    operation_id: FullArtifactSectionId

    def apply_to(self, state: "MutableState") -> None:
        task = Task.build(state.next_task_id())

        state.add_task(task)

        work_unit = WorkUnit.build(id=state.next_work_unit_id(), task_id=task.id, operation_id=self.operation_id)

        state.add_work_unit(work_unit)

        state.mark_started()


class ChangeRemoveTask(Change):
    task_id: TaskId

    def apply_to(self, state: "MutableState") -> None:
        state.remove_task(self.task_id)


class ChangeAddActionRequest(Change):
    action_request: ActionRequest

    def apply_to(self, state: "MutableState") -> None:
        state.add_action_request(self.action_request)


class ChangeRemoveActionRequest(Change):
    action_request_id: ActionRequestId

    def apply_to(self, state: "MutableState") -> None:
        state.remove_action_request(self.action_request_id)


class ChangeRemoveWorkUnit(Change):
    work_unit_id: WorkUnitId

    def apply_to(self, state: "MutableState") -> None:
        state.remove_work_unit(self.work_unit_id)


class ChangeSetTaskContext(Change):
    task_id: TaskId
    key: str
    value: object

    def apply_to(self, state: "MutableState") -> None:
        target_task: Task | None = None
        for task in state.tasks:
            if task.id == self.task_id:
                target_task = task
                break

        assert target_task is not None

        target_task.context[self.key] = self.value
