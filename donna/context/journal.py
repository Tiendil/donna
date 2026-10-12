from __future__ import annotations

from llm_tool_cli.config.runtime import runtime_config
from llm_tool_cli.core.result import Ok, Result, unwrap_to_error
from llm_tool_cli.protocol import Protocol
from llm_tool_cli.protocol import errors as protocol_errors

from donna.context.output import output
from donna.core.utils import now
from donna.domain.internal_ids import TaskId
from donna.machine.caches import caches
from donna.machine.context import execution_context
from donna.protocol import journal as protocol_journal
from donna.workspaces import journal as workspace_journal


class Journal:
    __slots__ = ()

    def smart_actor_id(self) -> str:
        match runtime_config.get().protocol:
            case Protocol.human:
                return "human"
            case Protocol.llm:
                return "agent"
            case Protocol.automation:
                return "automation"
            case _:
                raise protocol_errors.UnsupportedFormatterMode(details={"mode": runtime_config.get().protocol})

    @unwrap_to_error
    def add(
        self,
        message: str,
        actor_id: str | None = None,
    ) -> Result[protocol_journal.JournalRecord]:
        if actor_id is None:
            actor_id = self.smart_actor_id()

        state = caches.get().state.load().unwrap()
        parsed_task_id: TaskId | None = state.current_task.id if state.current_task else None
        execution = execution_context.get()

        record = protocol_journal.JournalRecord(
            timestamp=now(),
            actor_id=actor_id,
            message=message,
            current_task_id=parsed_task_id,
            current_work_unit_id=execution.current_work_unit_id,
            current_operation_id=execution.current_operation_id,
        )

        workspace_journal.write_record(record).unwrap()
        output.get().emit_journal(record)

        return Ok(record)
