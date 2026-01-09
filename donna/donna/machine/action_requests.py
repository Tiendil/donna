import textwrap

from donna.core.entities import BaseEntity
from donna.domain.ids import next_id, OperationId, FullArtifactLocalId
from donna.domain.types import (
    ActionRequestId,
)
from donna.machine.cells import Cell
from donna.world import navigator


class ActionRequest(BaseEntity):
    id: ActionRequestId
    request: str
    operation_id: FullArtifactLocalId

    @classmethod
    def build(cls, request: str, operation_id: FullArtifactLocalId) -> "ActionRequest":
        return cls(
            id=next_id(ActionRequestId),
            request=request,
            operation_id=operation_id,
        )

    def cells(self) -> list[Cell]:
        from donna.world.primitives_register import register

        workflow = navigator.get_artifact(self.operation_id.full_artifact_id)

        operation = workflow.get_operation(self.operation_id.local_id)

        assert operation is not None

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

        for result in operation.results:
            cells.extend(result.cells())

        return cells
