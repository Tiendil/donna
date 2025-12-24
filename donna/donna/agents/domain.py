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


class AgentCellHistory(BaseEntity):
    work_unit_id: WorkUnitId | None
    body: str


class AgentCell(BaseEntity):
    story_id: StoryId | None
    task_id: TaskId | None
    work_unit_id: WorkUnitId | None

    def render(self) -> AgentCellHistory:

        cell = textwrap.dedent(
            """
        ##########################
        {meta}
        --------------------------
        {custom_body}
        """
        ).format(custom_body=self.custom_body(), meta=self.render_meta())

        return AgentCellHistory(work_unit_id=self.work_unit_id, body=cell.strip())

    def meta(self) -> dict[str, str]:
        return {
            "story_id": str(self.story_id),
            "task_id": str(self.task_id) if self.task_id is not None else "",
            "work_unit_id": (str(self.work_unit_id) if self.work_unit_id is not None else ""),
        }

    def render_meta(self) -> str:
        meta_lines = [f"{key}: {value}" for key, value in self.meta().items()]
        return "\n".join(meta_lines)

    def custom_body(self) -> str:
        raise NotImplementedError()


class AgentMessage(AgentCell):
    message: str
    action_request_id: ActionRequestId | None

    def meta(self) -> dict[str, str]:
        base_meta = super().meta()

        base_meta["action_request_id"] = str(self.action_request_id) if self.action_request_id is not None else ""

        return base_meta

    def custom_body(self) -> str:
        return self.message


class AgentArtifact(AgentCell):
    artifact_id: ArtifactId
    content_type: str
    description: str
    content: str

    def meta(self) -> dict[str, str]:
        base_meta = super().meta()
        base_meta.update(
            {
                "artifact_id": str(self.artifact_id),
                "artifact_content_type": self.content_type,
                "artifact_description": self.description,
            }
        )
        return base_meta

    def custom_body(self) -> str:
        return self.content


class WorkflowCell(AgentCell):
    workflow_id: str
    name: str
    description: str

    def meta(self) -> dict[str, str]:
        base_meta = super().meta()
        base_meta["workflow_id"] = self.workflow_id
        return base_meta

    def custom_body(self) -> str:
        return f"# Workflow: {self.name}\n\n{self.description}"


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
        from donna.workflows.operations import storage

        results = []

        operation = storage().get(self.operation_id)

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
