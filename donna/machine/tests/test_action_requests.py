from donna.machine.action_requests import ActionRequest, ActionRequestNode
from donna.machine.tests import make
from donna.protocol import ActionRequestCell


class TestActionRequest:
    def test_build__creates_pending_request_without_id(self) -> None:
        request = ActionRequest.build(
            title="Need input",
            request="Choose next step",
            operation_id=make.PRIMARY_OPERATION_ID,
        )

        assert request.id is None
        assert request.title == "Need input"
        assert request.request == "Choose next step"
        assert request.operation_id == make.PRIMARY_OPERATION_ID

    def test_node__returns_action_request_node(self) -> None:
        request = make.action_request()

        node = request.node()

        assert isinstance(node, ActionRequestNode)


class TestActionRequestNode:
    def test_status__returns_action_request_status_cell(self) -> None:
        request = make.action_request()

        cell = ActionRequestNode(request).status()

        assert isinstance(cell, ActionRequestCell)
        assert cell.action_request_id == request.id
        assert cell.request == request.request
