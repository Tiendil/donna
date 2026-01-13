from typing import TYPE_CHECKING

from donna.domain.ids import ActionRequestId, FullArtifactLocalId, TaskId, WorkUnitId
from donna.machine.action_requests import ActionRequest
from donna.machine.tasks import Task, WorkUnit

if TYPE_CHECKING:
    from donna.machine.state import MutableState


class Change:
    def apply_to(self, state: "MutableState") -> None:
        raise NotImplementedError()


class ChangeFinishTask(Change):
    def __init__(self, task_id: TaskId) -> None:
        self.task_id = task_id

    def apply_to(self, state: "MutableState") -> None:
        state.finish_workflow(self.task_id)


class ChangeAddWorkUnit(Change):
    def __init__(self, task_id: TaskId, operation_id: FullArtifactLocalId) -> None:
        self.task_id = task_id
        self.operation_id = operation_id

    def apply_to(self, state: "MutableState") -> None:
        work_unit = WorkUnit.build(id=state.next_work_unit_id(), task_id=self.task_id, operation_id=self.operation_id)
        state.add_work_unit(work_unit)


class ChangeAddTask(Change):
    def __init__(self, operation_id: FullArtifactLocalId) -> None:
        self.operation_id = operation_id

    def apply_to(self, state: "MutableState") -> None:
        task = Task.build(state.next_task_id())

        state.add_task(task)

        work_unit = WorkUnit.build(id=state.next_work_unit_id(), task_id=task.id, operation_id=self.operation_id)

        state.add_work_unit(work_unit)

        state.mark_started()


class ChangeRemoveTask(Change):
    def __init__(self, task_id: TaskId) -> None:
        self.task_id = task_id

    def apply_to(self, state: "MutableState") -> None:
        state.remove_task(self.task_id)


class ChangeAddActionRequest(Change):
    def __init__(self, action_request: ActionRequest) -> None:
        self.action_request = action_request

    def apply_to(self, state: "MutableState") -> None:
        state.add_action_request(self.action_request)


class ChangeRemoveActionRequest(Change):
    def __init__(self, action_request_id: ActionRequestId) -> None:
        self.action_request_id = action_request_id

    def apply_to(self, state: "MutableState") -> None:
        state.remove_action_request(self.action_request_id)


class ChangeRemoveWorkUnit(Change):
    def __init__(self, work_unit_id: WorkUnitId) -> None:
        self.work_unit_id = work_unit_id

    def apply_to(self, state: "MutableState") -> None:
        state.remove_work_unit(self.work_unit_id)
