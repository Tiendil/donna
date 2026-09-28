from donna.protocol.journal import JournalRecord
from donna.protocol.journal_formatters.base import Formatter as BaseFormatter


class Formatter(BaseFormatter):
    __slots__ = ()

    def format_journal(self, record: JournalRecord) -> bytes:
        timestamp = record.timestamp.time().isoformat("seconds")
        actor_id = record.actor_id or "-"
        current_task_id = record.current_task_id.short if record.current_task_id is not None else "-"
        output = f"{timestamp} [{current_task_id}] <{actor_id}> {record.message}"
        return (output + "\n").encode("utf-8")
