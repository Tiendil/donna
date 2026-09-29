import pytest
from llm_tool_cli.protocol import Protocol

from donna.domain.internal_ids import ActionRequestId
from donna.machine.tests import make
from donna.protocol import ActionRequestCell
from donna.protocol.logic_cells.tests.helpers import project


class TestActionRequestCell:
    @pytest.mark.parametrize("protocol", list(Protocol))
    @pytest.mark.parametrize("request_id", [make.ACTION_REQUEST_ID, None])
    def test_render__preserves_request_instruction_and_id(
        self, protocol: Protocol, request_id: ActionRequestId | None
    ) -> None:
        cell = ActionRequestCell(action_request_id=request_id, request="Do the thing")

        output = project(cell, protocol)

        assert output.model_dump(exclude={"id"}) == {
            "kind": "action_request",
            "media_type": "text/markdown",
            "content": (
                "**This is an action request for the agent. You MUST follow the instructions below.**\n\n"
                "Do the thing"
            ),
            "meta": {"action_request_id": str(request_id)},
        }
