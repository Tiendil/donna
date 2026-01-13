from typing import cast
import copy
import contextlib

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
from donna.machine.changes import (
    Change,
    ChangeAddTask,
    ChangeAddToQueue,
    ChangeRemoveActionRequest,
    ChangeRemoveWorkUnitFromQueue,
    ChangeAddWorkUnit,
    ChangeAddTask,
    ChangeRemoveTask,
    ChangeRemoveWork
)
from donna.machine.tasks import Task, WorkUnit
from donna.std.code.workflows import Workflow
from donna.world import artifacts
from donna.world.config import config


class BaseState(BaseEntity):
    active_tasks: list[Task]  # TODO: rename task to workflow?
    queue: list[WorkUnit]  # TODO: rename from queue, because it's not a queue anymore
    action_requests: list[ActionRequest]
    started: bool
    last_id: int

    @property
    def is_completed(self) -> bool:
        # A state can not consider itself completed if it was never started
        # it is important to distinguish sessions with unfinished initialization and sessions that are done
        return not self.active_tasks and self.started and not self.action_requests

    def has_work(self) -> bool:
        return bool(self.queue)

    ###########
    # Accessors
    ###########

    @property
    def current_task(self) -> Task:
        return self.active_tasks[-1]

    def get_task(self, task_id: TaskId) -> Task:
        for task in self.active_tasks:
            if task.id == task_id:
                return task

        raise NotImplementedError(f"Task with id '{task_id}' not found in active tasks")

    def get_action_request(self, request_id: ActionRequestId) -> ActionRequest:
        for request in self.action_requests:
            if request.id == request_id:
                return request

        raise NotImplementedError(f"Action request with id '{request_id}' not found in state")

    def get_work_unit(self, work_unit_id: WorkUnitId) -> WorkUnit:
        for unit in self.queue:
            if unit.id == work_unit_id:
                return unit

        raise NotImplementedError(f"Work unit with id '{work_unit_id}' not found in state")

    def get_next_work_unit(self) -> WorkUnit | None:
        for work_unit in self.queue:
            if work_unit.task_id != self.current_task.id:
                continue

            return work_unit

        return None

    #######
    # Cells
    #######

    def cells_for_complete(self) -> Cell:
        return Cell.build_markdown(
            kind="work_is_completed",
            content=(
                "The work in this session is COMPLETED. You MUST STOP all your activities immediately. "
                "ASK THE USER for further instructions."
            ),
        )

    def cells_for_status(self) -> list[Cell]:
        return [
            Cell.build_meta(
                kind="state_status",
                active_tasks=len(self.active_tasks),
                queued_work_units=len(self.queue),
                pending_action_requests=len(self.action_requests),
                is_completed=self.is_completed,
            )
        ]

    def get_cells(self) -> list[Cell]:

        cells = []

        for action_request in self.action_requests:
            for cell in action_request.cells():
                cells.append(cell)

        if self.is_completed:
            cells.append(self.cells_for_complete())

        return cells


class ConsistentState(BaseState):

    def mutator(self) -> "MutatedState":
        return MutatedState.from_dict(copy.deepcopy(self.model_dump()))


class MutatedState(BaseState):
    model_config = pydantic.ConfigDict(frozen=False)

    @classmethod
    def build(cls) -> "MutatedState":
        return cls(
            active_tasks=[],
            action_requests=[],
            queue=[],
            started=False,
            last_id=0,
        )

    def freeze(self) -> ConsistentState:
        return ConsistentState.from_dict(copy.deepcopy(self.model_dump()))

    ################
    # Ids generation
    ################

    def next_id(self, prefix: str) -> InternalId:
        self.last_id += 1
        new_id = InternalId.build(prefix, self.last_id)
        return new_id

    def next_task_id(self) -> TaskId:
        return cast(TaskId, self.next_id("T"))

    def next_work_unit_id(self) -> WorkUnitId:
        return cast(WorkUnitId, self.next_id("WU"))

    def next_action_request_id(self) -> ActionRequestId:
        return cast(ActionRequestId, self.next_id("AR"))

    ##########
    # Mutators
    ##########

    def mark_started(self) -> None:
        self.started = True

    def add_action_request(self, action_request: ActionRequest) -> None:
        action_request.id = self.next_action_request_id()
        self.action_requests.append(action_request)

    def add_work_unit(self, work_unit: WorkUnit) -> None:
        self.queue.append(work_unit)

    def add_task(self, task: Task) -> None:
        self.active_tasks.append(task)

    def remove_action_request(self, request_id: ActionRequestId) -> None:
        self.action_requests = [request for request in self.action_requests if request.id != request_id]

    def remove_work_unit(self, work_unit_id: WorkUnitId) -> None:
        self.queue = [unit for unit in self.queue if unit.id != work_unit_id]

    def remove_task(self, task_id: TaskId) -> None:
        self.active_tasks = [task for task in self.active_tasks if task.id != task_id]

    def apply_changes(self, task: Task, changes: list[Change]) -> None:
        for change in changes:
            change.apply_to(self, task)

    ####################
    # Complex operations
    ####################

    def complete_action_request(self, request_id: ActionRequestId, next_operation_id: FullArtifactLocalId) -> None:
        changes = [ChangeAddWorkUnit(self.current_task.id, next_operation_id),
                   ChangeRemoveActionRequest(request_id)]
        self.apply_changes(self.current_task, changes)

    def start_workflow(self, full_operation_id: FullArtifactLocalId) -> None:
        changes = [ChangeAddTask(full_operation_id)]
        self.apply_changes(self.current_task, changes)

    def finish_workflow(self, task_id: TaskId) -> None:
        changes = [ChangeRemoveTask(task_id)]
        self.apply_changes(self.current_task, changes)

    def exectute_next_work_unit(self) -> None:
        next_work_unit = self.get_next_work_unit()

        changes = next_work_unit.run(self.current_task)
        changes.append(ChangeRemoveWork(next_work_unit.id))

        self.apply_changes(self.current_task, changes)

    # def run(self) -> None:
    #     while self.has_work():
    #         self.step()
