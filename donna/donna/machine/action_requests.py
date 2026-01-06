import textwrap

from donna.core.entities import BaseEntity
from donna.domain.ids import next_id
from donna.domain.types import (
    ActionRequestId,
    OperationId,
    StoryId,
)
from donna.machine.cells import Cell


class ActionRequest(BaseEntity):
    id: ActionRequestId
    story_id: StoryId
    request: str
    operation_id: OperationId

    @classmethod
    def build(
        cls, story_id: StoryId, request: str, operation_id: OperationId
    ) -> "ActionRequest":
        return cls(
            id=next_id(story_id, ActionRequestId),
            story_id=story_id,
            request=request,
            operation_id=operation_id,
        )

    def cells(self) -> list[Cell]:
        from donna.world.primitives_register import register

        results = []

        operation = register().operations.get(self.operation_id)

        for result in operation.results:
            results.append(f"- `{result.id}` — {result.description}")

        operation_results = "\n".join(results)

        message = textwrap.dedent(
            """
        **This is an action request for the agent. You MUST follow the instructions below.**

        {request}

        Possible results:

        {operation_results}
        """
        ).format(request=self.request, operation_results=operation_results)

        cells = []

        cells.append(
            Cell.build_markdown(
                kind="action_request",
                content=message,
                story_id=self.story_id,
                action_request_id=str(self.id),
            )
        )

        return cells
