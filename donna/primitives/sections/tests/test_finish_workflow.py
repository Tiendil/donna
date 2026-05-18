from typing import Any

from donna.machine.changes import ChangeFinishTask
from donna.machine.operations import FsmMode, OperationMeta
from donna.primitives.sections.finish_workflow import FinishWorkflow, FinishWorkflowConfig
from donna.primitives.tests import make


class TestFinishWorkflow:
    def test_markdown_construct_meta__creates_final_operation_without_transitions(self) -> None:
        result = FinishWorkflow().markdown_construct_meta(
            artifact_id=make.ARTIFACT_ID,
            source=make.section_source(),
            section_config=FinishWorkflowConfig(id=make.DONE_SECTION_ID, kind=make.FINISH_WORKFLOW_KIND),
            description="done",
        )

        assert result.is_ok()
        meta = result.unwrap()
        assert isinstance(meta, OperationMeta)
        assert meta.fsm_mode == FsmMode.final
        assert meta.allowed_transtions == set()

    def test_execute_section__emits_message_and_finishes_task(self, mocker: Any) -> None:
        runtime_context = make.FakeRuntimeContext()
        mocker.patch("donna.primitives.sections.finish_workflow.context", return_value=runtime_context)
        artifact = make.artifact(
            [
                make.artifact_section(
                    id=make.DONE_SECTION_ID,
                    description="Finished",
                    meta=OperationMeta(fsm_mode=FsmMode.final, allowed_transtions=set()),
                )
            ]
        )

        result = FinishWorkflow().execute_section(make.task(), make.work_unit(), artifact, make.DONE_SECTION_ID)

        assert result.is_ok()
        cell = runtime_context.output.cells[0]
        assert cell.kind == "info"
        assert cell.content == "Finished"
        change = result.unwrap()[0]
        assert isinstance(change, ChangeFinishTask)
        assert change.task_id == make.TASK_ID
