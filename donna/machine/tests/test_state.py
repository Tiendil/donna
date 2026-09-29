from llm_tool_cli.core.result import Ok, Result

from donna.domain.internal_ids import TaskId, WorkUnitId
from donna.machine import errors as machine_errors
from donna.machine.changes import Change, ChangeSetTaskContext
from donna.machine.context import reset_context, set_context
from donna.machine.operations import OperationKind
from donna.machine.state import MutableState
from donna.machine.tasks import Task, WorkUnit
from donna.machine.tests import make
from donna.machine.tests.helpers import FakeMachineContext
from donna.protocol import ActionRequestCell, SessionStateCell


class _StateOperation(OperationKind):
    def execute_section(
        self,
        task: Task,
        unit: WorkUnit,
        artifact: object,
        section_id: object,
    ) -> Result[list[Change]]:
        return Ok([ChangeSetTaskContext(task_id=task.id, key="status", value="done")])


class TestBaseState:
    def test_has_work__depends_on_queued_work_units(self) -> None:
        assert not make.mutable_state(work_units=[]).has_work()
        assert make.mutable_state(work_units=[make.work_unit()]).has_work()

    def test_current_task__returns_last_task(self) -> None:
        first = make.task(id=make.TASK_ID)
        second = make.task(id=TaskId("T-2-c"))
        state = make.mutable_state(tasks=[first, second])

        assert state.current_task == second

    def test_current_task__returns_none_without_tasks(self) -> None:
        assert make.mutable_state(tasks=[]).current_task is None

    def test_get_action_request__returns_matching_request(self) -> None:
        request = make.action_request()
        state = make.mutable_state(action_requests=[request])

        result = state.get_action_request(make.ACTION_REQUEST_ID)

        assert result.is_ok()
        assert result.unwrap() == request

    def test_get_action_request__reports_missing_request(self) -> None:
        result = make.mutable_state(action_requests=[]).get_action_request(make.ACTION_REQUEST_ID)

        assert result.is_err()
        error = result.unwrap_err()[0]
        assert isinstance(error, machine_errors.ActionRequestNotFound)
        assert error.request_id == make.ACTION_REQUEST_ID

    def test_get_next_work_unit__returns_first_unit_for_current_task(self) -> None:
        older_task = make.task(id=make.TASK_ID)
        current_task = make.task(id=TaskId("T-2-c"))
        older_unit = make.work_unit(task_id=older_task.id)
        current_unit = make.work_unit(id=WorkUnitId("WU-3-d"), task_id=current_task.id)
        state = make.mutable_state(tasks=[older_task, current_task], work_units=[older_unit, current_unit])

        assert state.get_next_work_unit() == current_unit


class TestMutableState:
    def test_build__creates_empty_not_started_state(self) -> None:
        state = MutableState.build()

        assert state.tasks == []
        assert state.work_units == []
        assert state.action_requests == []
        assert not state.started
        assert state.last_id == 0

    def test_next_ids__increment_shared_counter(self) -> None:
        state = MutableState.build()

        assert state.next_task_id() == "T-1-b"
        assert state.next_work_unit_id() == "WU-2-c"
        assert state.next_action_request_id() == "AR-3-d"
        assert state.last_id == 3

    def test_freeze_and_mutator__deep_copy_state(self) -> None:
        state = make.mutable_state(tasks=[make.task()])

        frozen = state.freeze()
        state.tasks[0].context["changed"] = True
        mutable = frozen.mutator()
        mutable.tasks[0].context["mutable"] = True

        assert frozen.tasks[0].context == {}
        assert mutable.tasks[0].context == {"mutable": True}

    def test_add_action_request__assigns_id_and_logs_request(self) -> None:
        state = make.mutable_state(last_id=2)
        request = make.action_request(id=None)
        machine_context = FakeMachineContext()
        token = set_context(machine_context)

        try:
            state.add_action_request(request)
        finally:
            reset_context(token)

        assert state.action_requests == [request.replace(id=make.ACTION_REQUEST_ID)]
        assert machine_context.journal.records == [
            {"message": "Request agent action `Action title`", "actor_id": "donna"}
        ]

    def test_apply_changes__applies_changes_in_order(self) -> None:
        state = make.mutable_state(tasks=[make.task()])

        state.apply_changes([ChangeSetTaskContext(task_id=make.TASK_ID, key="first", value=1)])

        assert state.tasks[0].context == {"first": 1}

    def test_complete_action_request__queues_next_work_unit_and_removes_request(self) -> None:
        task = make.task()
        request = make.action_request()
        state = make.mutable_state(tasks=[task], action_requests=[request], last_id=2)
        machine_context = FakeMachineContext()
        token = set_context(machine_context)

        try:
            result = state.complete_action_request(make.ACTION_REQUEST_ID, make.SECONDARY_OPERATION_ID)
        finally:
            reset_context(token)

        assert result.is_ok()
        assert state.action_requests == []
        assert len(state.work_units) == 1
        assert state.work_units[0].id == "WU-3-d"
        assert state.work_units[0].task_id == task.id
        assert state.work_units[0].operation_id == make.SECONDARY_OPERATION_ID
        assert machine_context.journal.records == [
            {"message": "Complete agent action `Action title`", "actor_id": None}
        ]

    def test_start_workflow__creates_task_and_initial_work_unit(self) -> None:
        state = MutableState.build()
        artifact = make.artifact()
        machine_context = FakeMachineContext(artifact=artifact)
        token = set_context(machine_context)

        try:
            result = state.start_workflow(make.PRIMARY_OPERATION_ID)
        finally:
            reset_context(token)

        assert result.is_ok()
        assert state.started
        assert len(state.tasks) == 1
        assert state.tasks[0].id == "T-1-b"
        assert state.tasks[0].workflow_id == make.PRIMARY_OPERATION_ID
        assert len(state.work_units) == 1
        assert state.work_units[0].id == "WU-2-c"
        assert state.work_units[0].task_id == state.tasks[0].id
        assert machine_context.artifacts.viewed == [make.ARTIFACT_ID]
        assert machine_context.journal.records == [{"message": "Start workflow `Workflow`", "actor_id": None}]

    def test_finish_workflow__removes_task_and_logs_workflow_title(self) -> None:
        task = make.task()
        state = make.mutable_state(tasks=[task])
        machine_context = FakeMachineContext(artifact=make.artifact())
        token = set_context(machine_context)

        try:
            state.finish_workflow(task.id)
        finally:
            reset_context(token)

        assert state.tasks == []
        assert machine_context.journal.records == [{"message": "Finish workflow `Workflow`", "actor_id": None}]

    def test_execute_next_work_unit__applies_operation_changes_and_removes_unit(self) -> None:
        task = make.task()
        unit = make.work_unit()
        state = make.mutable_state(tasks=[task], work_units=[unit])
        machine_context = FakeMachineContext(artifact=make.artifact(), primitive=_StateOperation())
        token = set_context(machine_context)

        try:
            result = state.execute_next_work_unit()
        finally:
            reset_context(token)

        assert result.is_ok()
        assert state.work_units == []
        assert state.tasks[0].context == {"status": "done"}
        assert machine_context.current_work_unit_id.get() is None


class TestStateNode:
    def test_status__captures_counts_and_started_flag(self) -> None:
        state = make.mutable_state(
            tasks=[make.task()], work_units=[make.work_unit()], action_requests=[make.action_request()], started=True
        )

        cell = state.node().status()

        assert isinstance(cell, SessionStateCell)
        assert cell.started
        assert cell.tasks == 1
        assert cell.queued_work_units == 1
        assert cell.pending_action_requests == 1

    def test_status__captures_new_session(self) -> None:
        cell = MutableState.build().node().status()

        assert not cell.started
        assert cell.tasks == cell.queued_work_units == cell.pending_action_requests == 0

    def test_references__returns_action_request_nodes(self) -> None:
        request = make.action_request()
        references = make.mutable_state(action_requests=[request]).node().references()

        assert len(references) == 1
        cell = references[0].status()
        assert isinstance(cell, ActionRequestCell)
        assert cell.action_request_id == request.id
