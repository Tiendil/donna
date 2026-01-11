from typing import cast

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.ids import (
    ActionRequestId,
    FullArtifactLocalId,
    InternalId,
    OperationId,
    TaskId,
    WorkUnitId,
    WorldId,
)
from donna.machine.action_requests import ActionRequest
from donna.machine.cells import Cell
from donna.machine.changes import Change, ChangeRemoveWorkUnitFromQueue, ChangeTaskState
from donna.machine.tasks import Task, TaskState, WorkUnit, WorkUnitState
from donna.std.code.workflows import Workflow
from donna.world import artifacts
from donna.world.config import config


# TODO: somehow separate methods that save plan and those that do not
class Plan(BaseEntity):
    active_tasks: list[Task]
    queue: list[WorkUnit]  # TODO: rename from queue, because it's not a queue anymore
    action_requests: list[ActionRequest]
    last_cells: list[Cell]
    started: bool
    last_id: int

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)

    @classmethod
    def build(cls) -> "Plan":
        return cls(
            active_tasks=[],
            action_requests=[],
            queue=[],
            last_cells=[],
            started=False,
            last_id=0,
        )

    def start_workflow(self, full_operation_id: FullArtifactLocalId) -> None:
        task = Task.build(self.next_task_id())
        work_unit = WorkUnit.build(self.next_work_unit_id(), task.id, full_operation_id)
        self.add_task(task, work_unit)

    def add_action_request(self, action_request: ActionRequest) -> None:
        action_request.id = self.next_action_request_id()
        self.action_requests.append(action_request)

    def _next_id(self, prefix: str) -> InternalId:
        self.last_id += 1
        new_id = InternalId.build(prefix, self.last_id)
        return new_id

    def next_task_id(self) -> TaskId:
        return cast(TaskId, self._next_id("T"))

    def next_work_unit_id(self) -> WorkUnitId:
        return cast(WorkUnitId, self._next_id("WU"))

    def next_action_request_id(self) -> ActionRequestId:
        return cast(ActionRequestId, self._next_id("AR"))

    def add_task(self, task: Task, work_unit: WorkUnit) -> None:
        self.active_tasks.append(task)
        self.queue.append(work_unit)
        self.started = True

    def is_completed(self) -> bool:
        # A plan can not consider itself completed if it was never started
        # it is important to distinguish sessions with unfinished initialization and sessions that are done
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
        world = config().get_world(WorldId("session"))
        world.write_state("state.json", self.to_json().encode("utf-8"))

    @classmethod
    def load(cls) -> "Plan":
        world = config().get_world(WorldId("session"))
        return cls.from_json(world.read_state("state.json").decode("utf-8"))

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
                "The work in this session is COMPLETED. You MUST STOP all your activities immediately. "
                "ASK THE USER for further instructions."
            ),
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

    def status_cells(self) -> list[Cell]:
        return [
            Cell.build_meta(
                kind="plan_status",
                active_tasks=len(self.active_tasks),
                queued_work_units=len(self.queue),
                pending_action_requests=len(self.action_requests),
                is_completed=self.is_completed(),
            )
        ]

    def remove_action_request(self, request_id: ActionRequestId) -> None:
        self.action_requests = [request for request in self.action_requests if request.id != request_id]

    def complete_action_request(self, request_id: ActionRequestId, next_operation_id: FullArtifactLocalId) -> None:
        operation_id = self.get_action_request(request_id).operation_id

        workflow = cast(Workflow, artifacts.load_artifact(operation_id.full_artifact_id))

        operation = workflow.get_operation(cast(OperationId, operation_id.local_id))
        assert operation is not None

        if next_operation_id not in operation.allowed_transtions:
            raise NotImplementedError(f"Operation '{operation_id}' can not go to '{next_operation_id}'")

        current_task = self.active_tasks[-1]

        new_work_unit = WorkUnit.build(
            self.next_work_unit_id(), task_id=current_task.id, operation_id=next_operation_id
        )
        self.queue.append(new_work_unit)

        self.remove_action_request(request_id)

        self.save()
