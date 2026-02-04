import copy
import textwrap
from typing import Sequence, cast

import pydantic

from donna.core.entities import BaseEntity
from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result, unwrap_to_error
from donna.domain.ids import (
    ActionRequestId,
    FullArtifactSectionId,
    InternalId,
    TaskId,
    WorkUnitId,
)
from donna.machine import errors as machine_errors
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
from donna.protocol.nodes import Node


class BaseState(BaseEntity):
    tasks: list[Task]
    work_units: list[WorkUnit]
    action_requests: list[ActionRequest]
    started: bool
    last_id: int

    def has_work(self) -> bool:
        return bool(self.work_units)

    def node(self) -> "StateNode":
        return StateNode(self)

    ###########
    # Accessors
    ###########

    @property
    def current_task(self) -> Task:
        return self.tasks[-1]

    def get_action_request(self, request_id: ActionRequestId) -> Result[ActionRequest, ErrorsList]:
        for request in self.action_requests:
            if request.id == request_id:
                return Ok(request)

        return Err([machine_errors.ActionRequestNotFound(request_id=request_id)])

    # Currently we execute first work unit found for the current task
    # Since we only append work units, this effectively works as a queue per task
    # In the future we may want to have more sophisticated scheduling
    def get_next_work_unit(self) -> WorkUnit | None:
        for work_unit in self.work_units:
            if work_unit.task_id != self.current_task.id:
                continue

            return work_unit

        return None


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
        full_request = action_request.replace(id=self.next_action_request_id())
        self.action_requests.append(full_request)

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

    @unwrap_to_error
    def exectute_next_work_unit(self) -> Result[None, ErrorsList]:
        next_work_unit = self.get_next_work_unit()
        assert next_work_unit is not None

        changes = next_work_unit.run(self.current_task).unwrap()
        changes.append(ChangeRemoveWorkUnit(work_unit_id=next_work_unit.id))

        self.apply_changes(changes)
        return Ok(None)


class StateNode(Node):
    __slots__ = ("_state",)

    def __init__(self, state: BaseState) -> None:
        self._state = state

    def status(self) -> Cell:
        if not self._state.started:
            message = textwrap.dedent(
                """
            The session has not been started yet. You can safely start a new session and then run a workflow.
                """
            )

        elif not self._state.tasks:
            message = textwrap.dedent(
                """
            The session is IDLE. There are no active tasks.

            - If the developer asked you to start working on a new task, you can do so by running a new workflow.
            - If you have been working on a task, consider it completed and REPORT THE RESULTS TO THE DEVELOPER.
                """
            )

        elif self._state.work_units:
            message = textwrap.dedent(
                """
            The session has PENDING WORK UNITS. Donna has work to complete.

            - If the developer asked you to start working on a new task, you MUST warn that there are pending work
              units and ask if you should start a new session or continue working on the current work units.
            - If you have been working on a task, you can continue session.
                """
            )

        elif self._state.action_requests:
            message = textwrap.dedent(
                """
            The session is AWAITING YOUR ACTION. You have pending action requests to address.

            - If the developer asked you to start working on a new task, you MUST ask if you should start a new session
              or continue working on the current action requests.
            - Otherwise, you MUST address the pending action requests before proceeding.
                """
            )

        elif self._state.tasks:
            message = textwrap.dedent(
                """
            The session has unfinished TASKS but no pending work units or action requests.

            - If the developer asked you to start working on a new task , you MUST ask if you should start a new
              session or run a new workflow in the current one.
            - If you have been working on a task, you can consider it completed and output the results to the
              developer.
                """
            )

        else:
            raise machine_errors.SessionStateStatusInvalid()

        return Cell.build_markdown(
            kind="session_state_status",
            content=message,
            tasks=len(self._state.tasks),
            queued_work_units=len(self._state.work_units),
            pending_action_requests=len(self._state.action_requests),
        )

    def references(self) -> list[Node]:
        return [action_request.node() for action_request in self._state.action_requests]
