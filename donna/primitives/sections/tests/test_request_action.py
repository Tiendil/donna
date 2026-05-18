import pytest
from pydantic import ValidationError

from donna.domain.errors import InvalidIdentifier
from donna.machine.changes import ChangeAddActionRequest
from donna.machine.operations import FsmMode, OperationMeta
from donna.machine.tests import make as machine_make
from donna.primitives.sections.request_action import RequestAction, RequestActionConfig, extract_transitions
from donna.primitives.tests import make
from donna.workspaces.tests import make as workspace_make


class TestExtractTransitions:
    def test_extracts_unique_goto_directive_targets(self) -> None:
        text = "\n".join(
            [
                "$$donna goto next donna$$",
                "regular text",
                "$$donna   goto   done   donna$$",
                "$$donna goto next donna$$",
            ]
        )

        transitions = extract_transitions(text)

        assert transitions == {make.NEXT_SECTION_ID, make.DONE_SECTION_ID}

    def test_rejects_goto_target_that_is_not_a_section_id(self) -> None:
        with pytest.raises(InvalidIdentifier):
            extract_transitions("$$donna goto folder/next donna$$")


class TestRequestActionConfig:
    def test_validate_fsm_mode__rejects_final_mode(self) -> None:
        with pytest.raises(ValidationError):
            RequestActionConfig(
                id=make.START_SECTION_ID,
                kind=make.REQUEST_ACTION_KIND,
                fsm_mode=FsmMode.final,
            )


class TestRequestAction:
    def test_markdown_construct_meta__uses_analysis_markdown_for_allowed_transitions(self) -> None:
        source = workspace_make.section_source_from_markdown(
            "# Workflow\n\n## Ask\n\nChoose one.\n\n$$donna goto next donna$$\n",
            section_index=1,
        )

        result = RequestAction().markdown_construct_meta(
            artifact_id=machine_make.ARTIFACT_ID,
            source=source,
            section_config=RequestActionConfig(id=make.START_SECTION_ID, kind=make.REQUEST_ACTION_KIND),
            description="Choose one.",
        )

        assert result.is_ok()
        meta = result.unwrap()
        assert isinstance(meta, OperationMeta)
        assert meta.allowed_transtions == {make.NEXT_SECTION_ID}

    def test_execute_section__adds_action_request_for_current_operation(self) -> None:
        artifact = machine_make.artifact(
            [
                machine_make.artifact_section(
                    id=make.START_SECTION_ID,
                    kind=make.REQUEST_ACTION_KIND,
                    title="Ask agent",
                    description="Do the work",
                    meta=OperationMeta(fsm_mode=FsmMode.normal, allowed_transtions={make.NEXT_SECTION_ID}),
                )
            ]
        )

        result = RequestAction().execute_section(
            machine_make.task(),
            machine_make.work_unit(operation_id=make.START_OPERATION_ID),
            artifact,
            make.START_SECTION_ID,
        )

        assert result.is_ok()
        change = result.unwrap()[0]
        assert isinstance(change, ChangeAddActionRequest)
        assert change.action_request.id is None
        assert change.action_request.title == "Ask agent"
        assert change.action_request.request == "Do the work"
        assert change.action_request.operation_id == make.START_OPERATION_ID
