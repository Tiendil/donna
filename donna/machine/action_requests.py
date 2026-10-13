from llm_tool_cli.core.entities import BaseEntity

from donna.domain.artifact_ids import ArtifactSectionId
from donna.domain.internal_ids import ActionRequestId
from donna.protocol import ActionRequestCell


class ActionRequest(BaseEntity):
    id: ActionRequestId | None
    request: str
    operation_id: ArtifactSectionId
    title: str = "unknown"  # TODO: remove default value after 2026.05.01

    @classmethod
    def build(cls, title: str, request: str, operation_id: ArtifactSectionId) -> "ActionRequest":
        return cls(
            id=None,
            request=request,
            operation_id=operation_id,
            title=title,
        )

    def to_cell(self) -> ActionRequestCell:
        return ActionRequestCell(action_request_id=self.id, request=self.request)
