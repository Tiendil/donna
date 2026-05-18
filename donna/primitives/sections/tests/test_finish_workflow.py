from pytest_mock import MockerFixture

from donna.machine.changes import ChangeFinishTask
from donna.machine.operations import FsmMode, OperationMeta
from donna.machine.tests import make as machine_make
from donna.primitives.sections.finish_workflow import FinishWorkflow, FinishWorkflowConfig
from donna.primitives.tests import make
from donna.workspaces.tests import make as workspace_make


class TestFinishWorkflow:
    def test_markdown_construct_meta__creates_final_operation_without_transitions(self) -> None:
        result = FinishWorkflow().markdown_construct_meta(
            artifact_id=machine_make.ARTIFACT_ID,
            source=workspace_make.section_source(),
            section_config=FinishWorkflowConfig(
                id=make.section_id("done"),
                kind=make.primitive_kind("donna.primitives.sections.finish_workflow.FinishWorkflow"),
            ),
            description="done",
        )

        assert result.is_ok()
        meta = result.unwrap()
        assert isinstance(meta, OperationMeta)
        assert meta.fsm_mode == FsmMode.final
        assert meta.allowed_transitions == set()

    def test_execute_section__emits_message_and_finishes_task(self, mocker: MockerFixture) -> None:
        runtime_context = make.FakeRuntimeContext()
        mocker.patch("donna.primitives.sections.finish_workflow.context", return_value=runtime_context)
        artifact = machine_make.artifact(
            [
                machine_make.artifact_section(
                    id=make.section_id("done"),
                    kind=make.primitive_kind("donna.primitives.sections.finish_workflow.FinishWorkflow"),
                    description="Finished",
                    meta=OperationMeta(fsm_mode=FsmMode.final, allowed_transitions=set()),
                )
            ]
        )

        result = FinishWorkflow().execute_section(
            machine_make.task(), machine_make.work_unit(), artifact, make.section_id("done")
        )

        assert result.is_ok()
        cell = runtime_context.output.cells[0]
        assert cell.kind == "info"
        assert cell.content == "Finished"
        change = result.unwrap()[0]
        assert isinstance(change, ChangeFinishTask)
        assert change.task_id == machine_make.TASK_ID
