from typing import Any

from donna.machine.changes import ChangeAddWorkUnit
from donna.machine.operations import FsmMode
from donna.primitives.sections.output import Output, OutputConfig, OutputMeta, OutputMissingNextOperation
from donna.primitives.tests import make


class TestOutput:
    def test_markdown_construct_meta__records_next_operation_transition(self) -> None:
        result = Output().markdown_construct_meta(
            artifact_id=make.ARTIFACT_ID,
            source=make.section_source(),
            section_config=OutputConfig(
                id=make.START_SECTION_ID,
                kind=make.OUTPUT_KIND,
                fsm_mode=FsmMode.start,
                next_operation_id=make.NEXT_SECTION_ID,
            ),
            description="message",
        )

        assert result.is_ok()
        meta = result.unwrap()
        assert isinstance(meta, OutputMeta)
        assert meta.fsm_mode == FsmMode.start
        assert meta.next_operation_id == make.NEXT_SECTION_ID
        assert meta.allowed_transtions == {make.NEXT_SECTION_ID}

    def test_markdown_construct_meta__allows_missing_next_operation_for_validation(self) -> None:
        result = Output().markdown_construct_meta(
            artifact_id=make.ARTIFACT_ID,
            source=make.section_source(),
            section_config=OutputConfig(id=make.START_SECTION_ID, kind=make.OUTPUT_KIND),
            description="message",
        )

        assert result.is_ok()
        meta = result.unwrap()
        assert isinstance(meta, OutputMeta)
        assert meta.next_operation_id is None
        assert meta.allowed_transtions == set()

    def test_validate_section__requires_next_operation(self) -> None:
        artifact = make.artifact(
            [
                make.artifact_section(
                    id=make.START_SECTION_ID,
                    meta=OutputMeta(allowed_transtions=set(), next_operation_id=None),
                )
            ]
        )

        result = Output().validate_section(artifact, make.START_SECTION_ID)

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], OutputMissingNextOperation)

    def test_execute_section__emits_message_and_adds_next_work_unit(self, mocker: Any) -> None:
        runtime_context = make.FakeRuntimeContext()
        mocker.patch("donna.primitives.sections.output.context", return_value=runtime_context)
        artifact = make.artifact(
            [
                make.artifact_section(
                    id=make.START_SECTION_ID,
                    description="Agent message",
                    meta=OutputMeta(
                        allowed_transtions={make.NEXT_SECTION_ID},
                        next_operation_id=make.NEXT_SECTION_ID,
                    ),
                )
            ]
        )

        result = Output().execute_section(make.task(), make.work_unit(), artifact, make.START_SECTION_ID)

        assert result.is_ok()
        cell = runtime_context.output.cells[0]
        assert cell.kind == "info"
        assert cell.content == "Agent message"
        change = result.unwrap()[0]
        assert isinstance(change, ChangeAddWorkUnit)
        assert change.operation_id == make.ARTIFACT_ID + ":next"
