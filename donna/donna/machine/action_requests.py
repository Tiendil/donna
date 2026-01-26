import textwrap

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.ids import ActionRequestId, FullArtifactLocalId
from donna.protocol.cells import Cell


class ActionRequest(BaseEntity):
    id: ActionRequestId | None
    request: str
    operation_id: FullArtifactLocalId

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)

    @classmethod
    def build(cls, request: str, operation_id: FullArtifactLocalId) -> "ActionRequest":
        return cls(
            id=None,
            request=request,
            operation_id=operation_id,
        )

    def cells(self) -> list[Cell]:
        message = textwrap.dedent(
            """
        **This is an action request for the agent. You MUST follow the instructions below.**

        {request}
        """
        ).format(request=self.request)

        cells = []

        cells.append(
            Cell.build_markdown(
                kind="action_request",
                content=message,
                action_request_id=str(self.id),
            )
        )

        return cells
