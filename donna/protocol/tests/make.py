import datetime

from llm_tool_cli.protocol.logic_cells import ContentCell

from donna.domain.artifact_ids import ArtifactId, artifact_section_id
from donna.domain.ids import SectionId
from donna.domain.internal_ids import TaskId, WorkUnitId
from donna.protocol.journal import JournalRecord


def cell(**kwargs: object) -> ContentCell:
    values: dict[str, object] = {
        "kind": "sample_status",
        "media_type": "text/markdown",
        "content": "  Sample content.  ",
        "meta": {"zeta": 2, "alpha": "first", "enabled": True, "missing": None},
    }
    values.update(kwargs)
    return ContentCell.model_validate(values)


def journal_record(**kwargs: object) -> JournalRecord:
    values = {
        "timestamp": datetime.datetime(2026, 5, 18, 10, 30, 45, tzinfo=datetime.UTC),
        "actor_id": "agent",
        "message": "Completed step",
        "current_task_id": TaskId.build("task", 42),
        "current_work_unit_id": WorkUnitId.build("work-unit", 7),
        "current_operation_id": artifact_section_id(ArtifactId("@/workflow.donna.md"), SectionId("operation")),
    }
    values.update(kwargs)
    return JournalRecord.model_validate(values)
