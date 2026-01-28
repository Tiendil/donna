import textwrap

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.ids import ActionRequestId, FullArtifactSectionId
from donna.protocol.cells import Cell
from donna.protocol.nodes import Node


class ActionRequest(BaseEntity):
    id: ActionRequestId | None
    request: str
    operation_id: FullArtifactSectionId

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)

    @classmethod
    def build(cls, request: str, operation_id: FullArtifactSectionId) -> "ActionRequest":
        return cls(
            id=None,
            request=request,
            operation_id=operation_id,
        )

    def node(self) -> "ActionRequestNode":
        return ActionRequestNode(self)


class ActionRequestNode(Node):
    __slots__ = ("action_request",)

    def __init__(self, action_request: ActionRequest) -> None:
        self.action_request = action_request

    def status(self) -> Cell:
        message = textwrap.dedent(
            """
        **This is an action request for the agent. You MUST follow the instructions below.**

        {request}
        """
        ).format(request=self.action_request.request)

        return Cell.build_markdown(
            kind="action_request",
            content=message,
            action_request_id=str(self.action_request.id),
        )
