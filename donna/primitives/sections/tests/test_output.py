from pytest_mock import MockerFixture

from donna.machine.changes import ChangeAddWorkUnit
from donna.machine.operations import FsmMode
from donna.machine.tests import make as machine_make
from donna.primitives.sections.output import Output, OutputConfig, OutputMeta, OutputMissingNextOperation
from donna.primitives.tests import make
from donna.workspaces.tests import make as workspace_make


class TestOutput:
    def test_markdown_construct_meta__records_next_operation_transition(self) -> None:
        result = Output().markdown_construct_meta(
            artifact_id=machine_make.ARTIFACT_ID,
            source=workspace_make.section_source(),
            section_config=OutputConfig(
                id=make.section_id("start"),
                kind=make.primitive_kind("donna.primitives.sections.output.Output"),
                fsm_mode=FsmMode.start,
                next_operation_id=make.section_id("next"),
            ),
            description="message",
        )

        assert result.is_ok()
        meta = result.unwrap()
        assert isinstance(meta, OutputMeta)
        assert meta.fsm_mode == FsmMode.start
        assert meta.next_operation_id == make.section_id("next")
        assert meta.allowed_transitions == {make.section_id("next")}

    def test_markdown_construct_meta__allows_missing_next_operation_for_validation(self) -> None:
        result = Output().markdown_construct_meta(
            artifact_id=machine_make.ARTIFACT_ID,
            source=workspace_make.section_source(),
            section_config=OutputConfig(
                id=make.section_id("start"),
                kind=make.primitive_kind("donna.primitives.sections.output.Output"),
            ),
            description="message",
        )

        assert result.is_ok()
        meta = result.unwrap()
        assert isinstance(meta, OutputMeta)
        assert meta.next_operation_id is None
        assert meta.allowed_transitions == set()

    def test_validate_section__requires_next_operation(self) -> None:
        artifact = machine_make.artifact(
            [
                machine_make.artifact_section(
                    id=make.section_id("start"),
                    kind=make.primitive_kind("donna.primitives.sections.text.Text"),
                    meta=OutputMeta(allowed_transitions=set(), next_operation_id=None),
                )
            ]
        )

        result = Output().validate_section(artifact, make.section_id("start"))

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], OutputMissingNextOperation)

    def test_execute_section__emits_message_and_adds_next_work_unit(self, mocker: MockerFixture) -> None:
        runtime_context = make.FakeRuntimeContext()
        mocker.patch("donna.primitives.sections.output.context", return_value=runtime_context)
        artifact = machine_make.artifact(
            [
                machine_make.artifact_section(
                    id=make.section_id("start"),
                    kind=make.primitive_kind("donna.primitives.sections.text.Text"),
                    description="Agent message",
                    meta=OutputMeta(
                        allowed_transitions={make.section_id("next")},
                        next_operation_id=make.section_id("next"),
                    ),
                )
            ]
        )

        result = Output().execute_section(
            machine_make.task(),
            machine_make.work_unit(operation_id=make.operation_id("start")),
            artifact,
            make.section_id("start"),
        )

        assert result.is_ok()
        cell = runtime_context.output.cells[0]
        assert cell.kind == "info"
        assert cell.content == "Agent message"
        change = result.unwrap()[0]
        assert isinstance(change, ChangeAddWorkUnit)
        assert change.operation_id == machine_make.ARTIFACT_ID + ":next"
