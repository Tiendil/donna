from donna.core.errors import ErrorsList
from donna.core.result import Ok, Result, unwrap_to_error
from donna.core.utils import now
from donna.domain.artifact_ids import ArtifactSectionId
from donna.domain.internal_ids import TaskId, WorkUnitId
from donna.machine import errors as machine_errors
from donna.protocol import journal as protocol_journal
from donna.workspaces import journal as workspace_journal
from donna.workspaces.config import protocol as protocol_mode


def smart_agent_id() -> str:
    from donna.protocol.modes import Mode as ProtocolMode

    match protocol_mode():
        case ProtocolMode.human:
            return "human"
        case ProtocolMode.llm:
            return "agent"
        case ProtocolMode.automation:
            return "automation"
        case _:
            raise machine_errors.UnsupportedFormatterMode(mode=protocol_mode())


@unwrap_to_error
def add(  # noqa: CCR001
    message: str,
    actor_id: str | None = None,
) -> Result[protocol_journal.JournalRecord, ErrorsList]:
    from donna.context.context import context

    if actor_id is None:
        actor_id = smart_agent_id()

    ctx = context()
    state = ctx.state.load().unwrap()
    parsed_task_id: TaskId | None = state.current_task.id if state.current_task else None
    parsed_work_unit_id: WorkUnitId | None = ctx.current_work_unit_id.get()
    parsed_operation_id: ArtifactSectionId | None = ctx.current_operation_id.get()

    record = protocol_journal.JournalRecord(
        timestamp=now(),
        actor_id=actor_id,
        message=message,
        current_task_id=parsed_task_id,
        current_work_unit_id=parsed_work_unit_id,
        current_operation_id=parsed_operation_id,
    )

    workspace_journal.write_record(record).unwrap()
    ctx.output.emit_journal(record)

    return Ok(record)
