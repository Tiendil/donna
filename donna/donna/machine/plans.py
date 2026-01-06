import pydantic

from donna.core.entities import BaseEntity
from donna.domain.types import ActionRequestId, OperationResultId, StoryId, TaskId, WorkUnitId
from donna.machine.action_requests import ActionRequest
from donna.machine.cells import Cell
from donna.machine.changes import Change, ChangeRemoveWorkUnitFromQueue, ChangeTaskState
from donna.machine.tasks import Task, TaskState, WorkUnit, WorkUnitState
from donna.world.layout import layout
from donna.world.primitives_register import register


# TODO: somehow separate methods that save plan and those that do not
class Plan(BaseEntity):
    story_id: StoryId
    active_tasks: list[Task]
    queue: list[WorkUnit]  # TODO: rename from queue, because it's not a queue anymore
    action_requests: list[ActionRequest]
    last_cells: list[Cell]
    started: bool

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)

    @classmethod
    def build(cls, story_id: StoryId) -> "Plan":
        return cls(
            story_id=story_id,
            active_tasks=[],
            action_requests=[],
            queue=[],
            last_cells=[],
            started=False,
        )

    def add_task(self, task: Task, work_unit: WorkUnit) -> None:
        self.active_tasks.append(task)
        self.queue.append(work_unit)
        self.started = True

    def is_completed(self) -> bool:
        # A plan can not consider itself completed if it was never started
        # it is important to distinguish the stories with unfinished initialization and the stories that are done
        return not self.active_tasks and self.started and not self.action_requests

    def has_work(self) -> bool:
        return bool(self.queue)

    def get_task(self, task_id: TaskId) -> Task:
        for task in self.active_tasks:
            if task.id == task_id:
                return task

        raise NotImplementedError(f"Task with id '{task_id}' not found in active tasks")

    def get_action_request(self, request_id: ActionRequestId) -> ActionRequest:
        for request in self.action_requests:
            if request.id == request_id:
                return request

        raise NotImplementedError(f"Action request with id '{request_id}' not found in plan")

    def get_work_unit(self, work_unit_id: WorkUnitId) -> WorkUnit:
        for unit in self.queue:
            if unit.id == work_unit_id:
                return unit

        raise NotImplementedError(f"Work unit with id '{work_unit_id}' not found in plan")

    def save(self) -> None:
        layout().story_plan(self.story_id).write_text(self.to_json())

    @classmethod
    def load(cls, story_id: StoryId) -> "Plan":
        return cls.from_json(layout().story_plan(story_id).read_text())

    def get_next_work_unit(self) -> WorkUnit | None:
        task_id = self.active_tasks[-1].id

        for work_unit in self.queue:
            if work_unit.state != WorkUnitState.TODO:
                continue

            if work_unit.task_id != task_id:
                continue

            return work_unit

        return None

    def try_step(self, task: Task) -> list[Change]:  # noqa: CCR001
        changes: list[Change] = []

        if task.state == TaskState.TODO:
            changes.append(ChangeTaskState(TaskState.IN_PROGRESS))

        if task.state in (TaskState.COMPLETED, TaskState.FAILED):
            raise NotImplementedError(f"can not make step while in state {task.state}")

        if not self.queue:
            # TODO: we need to ensure that FSM will end with finish operation
            return changes

        next_work_unit = self.get_next_work_unit()

        if next_work_unit is None:
            return changes

        changes.extend(next_work_unit.run(task))

        if next_work_unit.state == WorkUnitState.COMPLETED:
            changes.append(ChangeRemoveWorkUnitFromQueue(next_work_unit.id))

        return changes

    def apply_changes(self, task: Task, changes: list[Change]) -> None:
        for change in changes:
            change.apply_to(self, task)

    def step(self) -> list[Cell]:
        task = self.active_tasks[-1]

        changes = self.try_step(task)
        self.apply_changes(task, changes)

        cells = list(self.last_cells)

        if task.state == TaskState.COMPLETED:
            self.active_tasks.pop()

        if task.state == TaskState.FAILED:
            raise NotImplementedError("Cannot step failed task")

        self.save()

        return cells

    def complete_message(self) -> Cell:
        return Cell.build_markdown(
            kind="work_is_completed",
            content=(
                "The work in this story is COMPLETED. You MUST STOP all your activities immediately. "
                "ASK THE USER for further instructions."
            ),
            story_id=self.story_id,
        )

    def run(self) -> list[Cell]:  # noqa: CCR001
        if self.is_completed():
            return [self.complete_message()]

        if not self.has_work():
            return []

        cells = self.step()

        while True:

            if self.is_completed():
                cells.append(self.complete_message())
                break

            if not self.has_work():
                break

            cells.extend(self.step())

        for action_request in self.action_requests:
            for cell in action_request.cells():
                cells.append(cell)

        return cells

    def remove_action_request(self, request_id: ActionRequestId) -> None:
        self.action_requests = [request for request in self.action_requests if request.id != request_id]

    def complete_action_request(self, request_id: ActionRequestId, result_id: OperationResultId) -> None:
        # if self.is_completed():
        #     raise NotImplementedError("Plan is already completed")

        operation_id = self.get_action_request(request_id).operation_id

        operation = register().operations.get(operation_id)

        result = operation.result(result_id)

        current_task = self.active_tasks[-1]

        new_work_unit = WorkUnit.build(story_id=self.story_id, task_id=current_task.id, operation=result.operation_id)
        self.queue.append(new_work_unit)

        self.remove_action_request(request_id)

        self.save()


def get_plan(story_id: StoryId) -> Plan:
    plan_path = layout().story_plan(story_id)

    if not plan_path.exists():
        raise NotImplementedError(f"Plan for story '{story_id}' does not exist")

    return Plan.from_json(plan_path.read_text())
