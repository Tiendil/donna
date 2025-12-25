import pydantic

from donna.machine.action_requests import ActionRequest
from donna.machine.cells import AgentCellHistory, AgentMessage
from donna.core.entities import BaseEntity
from donna.domain.layout import layout
from donna.domain.types import ActionRequestId, OperationResultId, StoryId, TaskId, WorkUnitId
from donna.stories.events import Event
from donna.workflows.changes import Change, ChangeRemoveWorkUnitFromQueue, ChangeTaskState
from donna.workflows.operations import storage
from donna.workflows.tasks import Task, TaskState, WorkUnit, WorkUnitState


# TODO: somehow separate methods that save plan and those that do not
class Plan(BaseEntity):
    story_id: StoryId
    active_tasks: list[Task]
    queue: list[WorkUnit]  # TODO: rename from queue, because it's not a queue anymore
    action_requests: list[ActionRequest]
    events: list[Event]
    last_cells: list[AgentCellHistory]
    started: bool

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)

    @classmethod
    def build(cls, story_id: StoryId) -> "Plan":
        return cls(
            story_id=story_id,
            active_tasks=[],
            action_requests=[],
            events=[],
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
        return not self.active_tasks and self.started

    def has_work(self) -> bool:
        return bool(self.active_tasks)

    def add_event(self, event: Event) -> None:
        self.events.append(event)

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
        layout().story_plan(self.story_id).write_text(self.to_toml())

    @classmethod
    def load(cls, story_id: StoryId) -> "Plan":
        return cls.from_toml(layout().story_plan(story_id).read_text())

    def apply_events(self) -> None:  # noqa: CCR001
        task_id = self.active_tasks[-1].id

        for event in self.events:
            for opeation in storage().all():
                for event_template in opeation.trigger_on:
                    if event_template.match(event):
                        # TODO: we may want store an event in the work unit
                        new_work_unit = WorkUnit.build(task_id=task_id, operation=opeation.id)
                        self.queue.append(new_work_unit)

        self.events.clear()

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
            changes.append(ChangeTaskState(TaskState.COMPLETED))
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

    def step(self) -> list[AgentCellHistory]:
        # apply events on the beginning of the step
        # to process events that
        self.apply_events()

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

    def complete_message(self) -> AgentMessage:
        return AgentMessage(
            story_id=self.story_id,
            task_id=None,
            work_unit_id=None,
            action_request_id=None,
            message=(
                "The work in this story is COMPLETED. You MUST STOP all your activities immediately. "
                "ASK THE USER for further instructions."
            ),
        )

    def run(self) -> list[AgentCellHistory]:  # noqa: CCR001
        if self.is_completed():
            return [self.complete_message().render()]

        if not self.has_work():
            return []

        cells = self.step()

        while True:

            if self.is_completed():
                cells.append(self.complete_message().render())
                break

            if not self.has_work():
                break

            if not self.events:
                break

            cells.extend(self.step())

        for action_request in self.action_requests:
            for cell in action_request.cells():
                cells.append(cell.render())

        return cells

    def remove_action_request(self, request_id: ActionRequestId) -> None:
        self.action_requests = [request for request in self.action_requests if request.id != request_id]

    def complete_action_request(self, request_id: ActionRequestId, result_id: OperationResultId) -> None:
        if self.is_completed():
            raise NotImplementedError("Plan is already completed")

        operation_id = self.get_action_request(request_id).operation_id

        operation = storage().get(operation_id)

        result = operation.result(result_id)

        current_task = self.active_tasks[-1]

        event = Event.build(id=result.event_id, operation_id=operation_id, task_id=current_task.id)

        self.add_event(event)
        self.remove_action_request(request_id)

        self.save()


def get_plan(story_id: StoryId) -> Plan:
    plan_path = layout().story_plan(story_id)

    if not plan_path.exists():
        raise NotImplementedError(f"Plan for story '{story_id}' does not exist")

    return Plan.from_toml(plan_path.read_text())
