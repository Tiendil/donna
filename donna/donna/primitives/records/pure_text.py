
from typing import Literal
from donna.domain.types import RecordId, RecordKindId, StoryId
from donna.primitives.records import base
from donna.machine.records import RecordKindItem, RecordIndexItem
from donna.machine.cells import AgentCell, AgentCellHistory


class PureText(RecordKindItem):
    kind: Literal["pure_text"] = "pure_text"
    media_type: str
    content: str

    def cells(self, story_id: StoryId, record: RecordIndexItem) -> list[AgentCellHistory]:
        return [
            AgentRecordPureText(
                story_id=story_id,
                task_id=None,
                work_unit_id=None,
                record_id=record.id,
                description=record.description,
                record_kind=self.kind,
                media_type=self.media_type,
                content=self.content,
            ).render()
        ]


class AgentRecordPureText(AgentCell):
    record_id: RecordId
    description: str

    record_kind: RecordKindId
    media_type: str

    content: str

    def meta(self) -> dict[str, str]:
        base_meta = super().meta()
        base_meta.update(
            {
                "record_id": str(self.record_id),
                "description": self.description,

                "record_kind": str(self.record_kind),
                "media_type": self.media_type,

            }
        )
        return base_meta

    def custom_body(self) -> str:
        return self.content


class PureTextKind(base.RecordKind):
    pass
