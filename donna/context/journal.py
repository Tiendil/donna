from __future__ import annotations

from typing import TYPE_CHECKING

from llm_tool_cli.core.result import Ok, Result, unwrap_to_error
from llm_tool_cli.protocol import Protocol
from llm_tool_cli.protocol import errors as protocol_errors

from donna.core.utils import now
from donna.domain.artifact_ids import ArtifactSectionId
from donna.domain.internal_ids import TaskId, WorkUnitId
from donna.protocol import journal as protocol_journal
from donna.workspaces import journal as workspace_journal
from donna.workspaces.config import protocol as protocol_mode

if TYPE_CHECKING:
    from donna.context.context import Context


class Journal:
    __slots__ = ("_context",)

    def __init__(self, context: Context) -> None:
        self._context = context

    def smart_actor_id(self) -> str:
        match protocol_mode():
            case Protocol.human:
                return "human"
            case Protocol.llm:
                return "agent"
            case Protocol.automation:
                return "automation"
            case _:
                raise protocol_errors.UnsupportedFormatterMode(details={"mode": protocol_mode()})

    @unwrap_to_error
    def add(
        self,
        message: str,
        actor_id: str | None = None,
    ) -> Result[protocol_journal.JournalRecord]:
        if actor_id is None:
            actor_id = self.smart_actor_id()

        state = self._context.state.load().unwrap()
        parsed_task_id: TaskId | None = state.current_task.id if state.current_task else None
        parsed_work_unit_id: WorkUnitId | None = self._context.current_work_unit_id.get()
        parsed_operation_id: ArtifactSectionId | None = self._context.current_operation_id.get()

        record = protocol_journal.JournalRecord(
            timestamp=now(),
            actor_id=actor_id,
            message=message,
            current_task_id=parsed_task_id,
            current_work_unit_id=parsed_work_unit_id,
            current_operation_id=parsed_operation_id,
        )

        workspace_journal.write_record(record).unwrap()
        self._context.output.emit_journal(record)

        return Ok(record)
