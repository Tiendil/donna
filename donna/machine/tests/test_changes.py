import pytest

from donna.domain.internal_ids import TaskId
from donna.machine.changes import (
    ChangeAddActionRequest,
    ChangeAddTask,
    ChangeAddWorkUnit,
    ChangeFinishTask,
    ChangeRemoveActionRequest,
    ChangeRemoveTask,
    ChangeRemoveWorkUnit,
    ChangeSetTaskContext,
)
from donna.machine.context import reset_context, set_context
from donna.machine.tests import make
from donna.machine.tests.helpers import FakeMachineContext


class TestChangeAddTask:
    def test_apply_to__adds_task_initial_work_unit_and_marks_started(self) -> None:
        state = make.mutable_state(started=False)

        ChangeAddTask(operation_id=make.PRIMARY_OPERATION_ID).apply_to(state)

        assert state.started
        assert len(state.tasks) == 1
        assert state.tasks[0].id == "T-1-b"
        assert len(state.work_units) == 1
        assert state.work_units[0].id == "WU-2-c"
        assert state.work_units[0].task_id == state.tasks[0].id
        assert state.work_units[0].operation_id == make.PRIMARY_OPERATION_ID


class TestChangeFinishTask:
    def test_apply_to__finishes_workflow_for_task(self) -> None:
        task = make.task()
        state = make.mutable_state(tasks=[task])
        machine_context = FakeMachineContext(artifact=make.artifact())
        token = set_context(machine_context)

        try:
            ChangeFinishTask(task_id=task.id).apply_to(state)
        finally:
            reset_context(token)

        assert state.tasks == []
        assert machine_context.journal.records == [{"message": "Finish workflow `Workflow`", "actor_id": None}]


class TestChangeAddWorkUnit:
    def test_apply_to__adds_work_unit_with_next_id(self) -> None:
        state = make.mutable_state(last_id=2)

        ChangeAddWorkUnit(task_id=make.TASK_ID, operation_id=make.SECONDARY_OPERATION_ID).apply_to(state)

        assert len(state.work_units) == 1
        assert state.work_units[0].id == "WU-3-d"
        assert state.work_units[0].task_id == make.TASK_ID
        assert state.work_units[0].operation_id == make.SECONDARY_OPERATION_ID


class TestChangeAddActionRequest:
    def test_apply_to__delegates_to_state_action_request_addition(self) -> None:
        state = make.mutable_state(last_id=2)
        request = make.action_request(id=None)
        machine_context = FakeMachineContext()
        token = set_context(machine_context)

        try:
            ChangeAddActionRequest(action_request=request).apply_to(state)
        finally:
            reset_context(token)

        assert state.action_requests == [request.replace(id=make.ACTION_REQUEST_ID)]


class TestChangeRemoveActionRequest:
    def test_apply_to__removes_matching_action_request(self) -> None:
        state = make.mutable_state(action_requests=[make.action_request()])

        ChangeRemoveActionRequest(action_request_id=make.ACTION_REQUEST_ID).apply_to(state)

        assert state.action_requests == []


class TestChangeRemoveWorkUnit:
    def test_apply_to__removes_matching_work_unit(self) -> None:
        state = make.mutable_state(work_units=[make.work_unit()])

        ChangeRemoveWorkUnit(work_unit_id=make.WORK_UNIT_ID).apply_to(state)

        assert state.work_units == []


class TestChangeRemoveTask:
    def test_apply_to__removes_matching_task(self) -> None:
        state = make.mutable_state(tasks=[make.task()])

        ChangeRemoveTask(task_id=make.TASK_ID).apply_to(state)

        assert state.tasks == []


class TestChangeSetTaskContext:
    def test_apply_to__updates_matching_task_context(self) -> None:
        target = make.task(id=make.TASK_ID)
        other = make.task(id=TaskId("T-2-c"))
        state = make.mutable_state(tasks=[target, other])

        ChangeSetTaskContext(task_id=make.TASK_ID, key="answer", value=42).apply_to(state)

        assert state.tasks[0].context == {"answer": 42}
        assert state.tasks[1].context == {}

    def test_apply_to__raises_when_task_is_missing(self) -> None:
        state = make.mutable_state(tasks=[make.task(id=TaskId("T-2-c"))])

        with pytest.raises(AssertionError):
            ChangeSetTaskContext(task_id=make.TASK_ID, key="answer", value=42).apply_to(state)

        assert state.tasks[0].context == {}
