from llm_tool_cli.protocol.logic_cells.journal import JournalCell as BaseJournalCell

from donna.domain.artifact_ids import ArtifactSectionId
from donna.domain.internal_ids import TaskId, WorkUnitId


class JournalCell(BaseJournalCell):
    current_task_id: TaskId | None = None
    current_work_unit_id: WorkUnitId | None = None
    current_operation_id: ArtifactSectionId | None = None

    def human_line(self) -> str:
        task = self.current_task_id.short if self.current_task_id is not None else "-"
        return f"{self.timestamp.time().isoformat('seconds')} [{task}] <{self.actor_id or '-'}> {self.message}"

    def llm_line(self) -> str:
        return (
            f"{self.timestamp.isoformat()} [{self.current_task_id or '-'}] <{self.actor_id or '-'}> "
            f"[{self.current_work_unit_id or '-'}] [{self.current_operation_id or '-'}] {self.message}"
        )
