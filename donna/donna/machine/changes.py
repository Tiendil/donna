import copy
from typing import TYPE_CHECKING, Any

from donna.domain.types import WorkUnitId
from donna.machine.action_requests import ActionRequest
from donna.machine.cells import AgentCell
from donna.machine.events import Event
from donna.machine.tasks import Task, TaskState, WorkUnit

if TYPE_CHECKING:
    from donna.machine.plans import Plan


class Change:
    def apply_to(self, plan: "Plan", task: Task) -> None:
        raise NotImplementedError()


class ChangeTaskState(Change):
    def __init__(self, new_state: TaskState) -> None:
        self.new_state = new_state

    def apply_to(self, plan: "Plan", task: Task) -> None:
        task.state = self.new_state


class ChangeTaskContext(Change):
    def __init__(self, new_context: dict[str, Any]) -> None:
        self.new_context = copy.deepcopy(new_context)

    def apply_to(self, plan: "Plan", task: Task) -> None:
        task.context.update(self.new_context)


class ChangeAddToQueue(Change):
    def __init__(self, unit: WorkUnit) -> None:
        self.unit = unit

    def apply_to(self, plan: "Plan", task: Task) -> None:
        plan.queue.append(self.unit)


class ChangeAddAgentCell(Change):
    def __init__(self, agent_cell: AgentCell) -> None:
        self.agent_cell = agent_cell

    def apply_to(self, plan: "Plan", task: Task) -> None:
        plan.last_cells.append(self.agent_cell.render())


class ChangeAddActionRequest(Change):
    def __init__(self, action_request: ActionRequest) -> None:
        self.action_request = action_request

    def apply_to(self, plan: "Plan", task: Task) -> None:
        plan.action_requests.append(self.action_request)


class ChangeRemoveWorkUnitFromQueue(Change):
    def __init__(self, work_unit_id: WorkUnitId) -> None:
        self.work_unit_id = work_unit_id

    def apply_to(self, plan: "Plan", task: Task) -> None:
        plan.queue = [item for item in plan.queue if item.id != self.work_unit_id]


class ChangeEvent(Change):
    def __init__(self, event: Event) -> None:
        self.event = event

    def apply_to(self, plan: "Plan", task: Task) -> None:
        plan.add_event(self.event)
