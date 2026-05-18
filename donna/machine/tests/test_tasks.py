from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result
from donna.domain.internal_ids import TaskId, WorkUnitId
from donna.machine.changes import Change, ChangeSetTaskContext
from donna.machine.context import reset_context, set_context
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
    ) -> Result[list[Change], ErrorsList]:
        return Ok(
            [
                ChangeSetTaskContext(
                    task_id=task.id,
                    key="executed",
                    value={
                        "unit_id": str(unit.id),
                        "section_id": str(section_id),
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

    def test_run__executes_operation_and_restores_scope(self) -> None:
        task = make.task()
        unit = make.work_unit()
        artifact = make.artifact()
        primitive = _ContextSettingOperation()
        machine_context = FakeMachineContext(artifact=artifact, primitive=primitive)
        token = set_context(machine_context)

        try:
            result = unit.run(task)
        finally:
            reset_context(token)

        assert result.is_ok()
        changes = result.unwrap()
        assert changes == [
            ChangeSetTaskContext(
                task_id=task.id,
                key="executed",
                value={"unit_id": str(unit.id), "section_id": str(make.PRIMARY_SECTION_ID)},
            )
        ]
        assert machine_context.artifacts.executed == [(make.ARTIFACT_ID, task, unit)]
        assert machine_context.primitives.resolved == [make.PRIMITIVE_PATH]
        assert machine_context.journal.records == [{"message": "Workflow", "actor_id": "donna"}]
        assert machine_context.current_operation_id.get() is None
