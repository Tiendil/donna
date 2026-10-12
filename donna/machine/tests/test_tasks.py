import pytest
from llm_tool_cli.core.errors import EnvironmentError
from llm_tool_cli.core.result import Ok, Result
from pytest_mock import MockerFixture

from donna.domain.internal_ids import TaskId, WorkUnitId
from donna.machine.changes import Change, ChangeSetTaskContext
from donna.machine.context import ExecutionContext, execution_context, reset_context, set_context
from donna.machine.operations import OperationKind
from donna.machine.tasks import Task, WorkUnit
from donna.machine.tests import make
from donna.machine.tests.helpers import FakeMachineContext


class _ContextSettingOperation(OperationKind):
    def execute_section(
        self,
        task: Task,
        unit: WorkUnit,
        artifact: object,
        section_id: object,
    ) -> Result[list[Change]]:
        return Ok(
            [
                ChangeSetTaskContext(
                    task_id=task.id,
                    key="executed",
                    value={
                        "unit_id": str(unit.id),
                        "section_id": str(section_id),
                        "execution": execution_context.get().model_dump(),
                    },
                )
            ]
        )


class TestTask:
    def test_build__creates_empty_context(self) -> None:
        task = Task.build(id=TaskId("T-1-b"), workflow_id=make.PRIMARY_OPERATION_ID)

        assert task.context == {}


class TestWorkUnit:
    def test_build__uses_empty_context_by_default(self) -> None:
        unit = WorkUnit.build(
            id=WorkUnitId("WU-1-b"),
            task_id=TaskId("T-1-b"),
            operation_id=make.PRIMARY_OPERATION_ID,
        )

        assert unit.context == {}

    def test_build__deep_copies_context(self) -> None:
        source_context = {"items": [1]}

        unit = WorkUnit.build(
            id=WorkUnitId("WU-1-b"),
            task_id=TaskId("T-1-b"),
            operation_id=make.PRIMARY_OPERATION_ID,
            context=source_context,
        )
        source_context["items"].append(2)

        assert unit.context == {"items": [1]}

    @pytest.mark.parametrize(
        "outer",
        [
            ExecutionContext(),
            ExecutionContext(
                current_work_unit_id=WorkUnitId("WU-9-j"), current_operation_id=make.SECONDARY_OPERATION_ID
            ),
        ],
    )
    def test_run__executes_operation_and_restores_scope(self, outer: ExecutionContext) -> None:
        task = make.task()
        unit = make.work_unit()
        artifact = make.artifact()
        primitive = _ContextSettingOperation()
        machine_context = FakeMachineContext(artifact=artifact, primitive=primitive)
        token = set_context(machine_context)

        try:
            with execution_context.scope(outer):
                result = unit.run(task)
                assert execution_context.get() == outer
        finally:
            reset_context(token)

        assert result.is_ok()
        changes = result.unwrap()
        assert changes == [
            ChangeSetTaskContext(
                task_id=task.id,
                key="executed",
                value={
                    "unit_id": str(unit.id),
                    "section_id": str(make.PRIMARY_SECTION_ID),
                    "execution": {
                        "current_work_unit_id": outer.current_work_unit_id,
                        "current_operation_id": unit.operation_id,
                    },
                },
            )
        ]
        assert machine_context.artifacts.executed == [(make.ARTIFACT_ID, task, unit)]
        assert machine_context.primitives.resolved == [make.PRIMITIVE_PATH]
        assert machine_context.journal.records == [{"message": "Workflow", "actor_id": "donna"}]
        assert not execution_context.is_set()

    @pytest.mark.parametrize("source", ["artifact", "primitive"])
    def test_run__restores_scope_after_environment_error(self, source: str) -> None:
        failure = EnvironmentError(code="unavailable", message="Unavailable")
        machine_context = FakeMachineContext(
            artifact=make.artifact(),
            artifact_error=[failure] if source == "artifact" else None,
            primitive_error=[failure] if source == "primitive" else None,
        )
        outer = ExecutionContext(
            current_work_unit_id=make.WORK_UNIT_ID, current_operation_id=make.SECONDARY_OPERATION_ID
        )
        token = set_context(machine_context)
        try:
            with execution_context.scope(outer):
                result = make.work_unit().run(make.task())
                assert result.unwrap_err() == [failure]
                assert execution_context.get() == outer
        finally:
            reset_context(token)

        assert not execution_context.is_set()

    def test_run__restores_scope_after_unexpected_exception(self, mocker: MockerFixture) -> None:
        failure = ValueError("unexpected defect")
        machine_context = FakeMachineContext(artifact=make.artifact(), primitive=_ContextSettingOperation())
        mocker.patch.object(_ContextSettingOperation, "execute_section", side_effect=failure)
        outer = ExecutionContext(
            current_work_unit_id=make.WORK_UNIT_ID, current_operation_id=make.SECONDARY_OPERATION_ID
        )
        token = set_context(machine_context)
        try:
            with execution_context.scope(outer):
                with pytest.raises(ValueError) as caught:
                    make.work_unit().run(make.task())
                assert caught.value == failure
                assert execution_context.get() == outer
        finally:
            reset_context(token)

        assert not execution_context.is_set()
