import copy
from typing import Sequence, cast

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.ids import (
    ActionRequestId,
    FullArtifactSectionId,
    InternalId,
    TaskId,
    WorkUnitId,
)
from donna.machine.action_requests import ActionRequest
from donna.machine.changes import (
    Change,
    ChangeAddTask,
    ChangeAddWorkUnit,
    ChangeRemoveActionRequest,
    ChangeRemoveTask,
    ChangeRemoveWorkUnit,
)
from donna.machine.tasks import Task, WorkUnit
from donna.protocol.cells import Cell


class BaseState(BaseEntity):
    tasks: list[Task]
    work_units: list[WorkUnit]
    action_requests: list[ActionRequest]
    started: bool
    last_id: int

    @property
    def is_completed(self) -> bool:
        # A state can not consider itself completed if it was never started
        # it is important to distinguish sessions with unfinished initialization and sessions that are done
        return not self.tasks and self.started and not self.action_requests

    def has_work(self) -> bool:
        return bool(self.work_units)

    ###########
    # Accessors
    ###########

    @property
    def current_task(self) -> Task:
        return self.tasks[-1]

    def get_task(self, task_id: TaskId) -> Task:
        for task in self.tasks:
            if task.id == task_id:
                return task

        raise NotImplementedError(f"Task with id '{task_id}' not found in active tasks")

    def get_action_request(self, request_id: ActionRequestId) -> ActionRequest:
        for request in self.action_requests:
            if request.id == request_id:
                return request

        raise NotImplementedError(f"Action request with id '{request_id}' not found in state")

    # Currently we execute first work unit found for the current task
    # Since we only append work units, this effectively works as a queue per task
    # In the future we may want to have more sophisticated scheduling
    def get_next_work_unit(self) -> WorkUnit | None:
        for work_unit in self.work_units:
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
                tasks=len(self.tasks),
                queued_work_units=len(self.work_units),
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

    def mutator(self) -> "MutableState":
        return MutableState.model_validate(copy.deepcopy(self.model_dump()))


class MutableState(BaseState):
    model_config = pydantic.ConfigDict(frozen=False)

    @classmethod
    def build(cls) -> "MutableState":
        return cls(
            tasks=[],
            action_requests=[],
            work_units=[],
            started=False,
            last_id=0,
        )

    def freeze(self) -> ConsistentState:
        return ConsistentState.model_validate(copy.deepcopy(self.model_dump()))

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
        self.work_units.append(work_unit)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def remove_action_request(self, request_id: ActionRequestId) -> None:
        self.action_requests = [request for request in self.action_requests if request.id != request_id]

    def remove_work_unit(self, work_unit_id: WorkUnitId) -> None:
        self.work_units = [unit for unit in self.work_units if unit.id != work_unit_id]

    def remove_task(self, task_id: TaskId) -> None:
        self.tasks = [task for task in self.tasks if task.id != task_id]

    def apply_changes(self, changes: Sequence[Change]) -> None:
        for change in changes:
            change.apply_to(self)

    ####################
    # Complex operations
    ####################

    def complete_action_request(self, request_id: ActionRequestId, next_operation_id: FullArtifactSectionId) -> None:
        changes = [
            ChangeAddWorkUnit(task_id=self.current_task.id, operation_id=next_operation_id),
            ChangeRemoveActionRequest(action_request_id=request_id),
        ]
        self.apply_changes(changes)

    def start_workflow(self, full_operation_id: FullArtifactSectionId) -> None:
        changes = [ChangeAddTask(operation_id=full_operation_id)]
        self.apply_changes(changes)

    def finish_workflow(self, task_id: TaskId) -> None:
        changes = [ChangeRemoveTask(task_id=task_id)]
        self.apply_changes(changes)

    def exectute_next_work_unit(self) -> None:
        next_work_unit = self.get_next_work_unit()
        assert next_work_unit is not None

        changes = next_work_unit.run(self.current_task)
        changes.append(ChangeRemoveWorkUnit(work_unit_id=next_work_unit.id))

        self.apply_changes(changes)
