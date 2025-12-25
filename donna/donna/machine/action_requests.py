import textwrap

from donna.core.entities import BaseEntity
from donna.domain.types import (
    ActionRequestId,
    ArtifactId,
    OperationId,
    StoryId,
    TaskId,
    WorkUnitId,
    new_action_request_id,
)
from donna.machine.cells import AgentMessage


class ActionRequest(BaseEntity):
    id: ActionRequestId
    story_id: StoryId
    request: str
    operation_id: OperationId

    @classmethod
    def build(cls, story_id: StoryId, request: str, operation_id: OperationId) -> "ActionRequest":
        return cls(
            id=new_action_request_id(),
            story_id=story_id,
            request=request,
            operation_id=operation_id,
        )

    def cells(self) -> list[AgentMessage]:
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

        return [
            AgentMessage(
                story_id=self.story_id,
                task_id=None,
                work_unit_id=None,
                action_request_id=self.id,
                message=message,
            )
        ]
