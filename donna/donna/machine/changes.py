import copy
from typing import TYPE_CHECKING, Any

from donna.domain.ids import ActionRequestId, WorkUnitId
from donna.machine.action_requests import ActionRequest
from donna.machine.cells import Cell
from donna.machine.tasks import Task, TaskState, WorkUnit

if TYPE_CHECKING:
    from donna.machine.state import State


class Change:
    def apply_to(self, state: "State", task: Task) -> None:
        raise NotImplementedError()


class ChangeTaskState(Change):
    def __init__(self, new_state: TaskState) -> None:
        self.new_state = new_state

    def apply_to(self, state: "State", task: Task) -> None:
        task.state = self.new_state


class ChangeTaskContext(Change):
    def __init__(self, new_context: dict[str, Any]) -> None:
        self.new_context = copy.deepcopy(new_context)

    def apply_to(self, state: "State", task: Task) -> None:
        task.context.update(self.new_context)


class ChangeAddToQueue(Change):
    def __init__(self, unit: WorkUnit) -> None:
        self.unit = unit

    def apply_to(self, state: "State", task: Task) -> None:
        state.queue.append(self.unit)


class ChangeAddCell(Change):
    def __init__(self, cell: Cell) -> None:
        self.cell = cell

    def apply_to(self, state: "State", task: Task) -> None:
        state.last_cells.append(self.cell)


class ChangeAddActionRequest(Change):
    def __init__(self, action_request: ActionRequest) -> None:
        self.action_request = action_request

    def apply_to(self, state: "State", task: Task) -> None:
        state.add_action_request(self.action_request)


class ChangeRemoveActionRequest(Change):
    def __init__(self, action_request_id: ActionRequestId) -> None:
        self.action_request_id = action_request_id

    def apply_to(self, state: "State", task: Task) -> None:
        state.action_requests = [req for req in state.action_requests if req.id != self.action_request_id]


class ChangeRemoveWorkUnitFromQueue(Change):
    def __init__(self, work_unit_id: WorkUnitId) -> None:
        self.work_unit_id = work_unit_id

    def apply_to(self, state: "State", task: Task) -> None:
        state.queue = [item for item in state.queue if item.id != self.work_unit_id]
