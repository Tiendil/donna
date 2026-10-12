from __future__ import annotations

from llm_tool_cli.core.context import ContextValue
from llm_tool_cli.core.entities import BaseEntity

from donna.domain.artifact_ids import ArtifactSectionId
from donna.domain.internal_ids import WorkUnitId


class ExecutionContext(BaseEntity):
    current_work_unit_id: WorkUnitId | None = None
    current_operation_id: ArtifactSectionId | None = None


execution_context = ContextValue[ExecutionContext]("donna_execution_context")
