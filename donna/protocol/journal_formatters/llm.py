from donna.protocol.journal import JournalRecord
from donna.protocol.journal_formatters.base import Formatter as BaseFormatter


class Formatter(BaseFormatter):
    __slots__ = ()

    def format_journal(self, record: JournalRecord) -> bytes:
        timestamp = record.timestamp.isoformat()
        actor_id = record.actor_id or "-"
        current_task_id = record.current_task_id or "-"
        current_work_unit_id = record.current_work_unit_id or "-"
        current_operation_id = record.current_operation_id or "-"

        output = (
            f"{timestamp} "
            f"[{current_task_id}] "
            f"<{actor_id}> "
            f"[{current_work_unit_id}] "
            f"[{current_operation_id}] "
            f"{record.message}"
        )
        return (output + "\n").encode("utf-8")
