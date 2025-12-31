from donna.domain.types import RecordKindId, StoryId
from donna.machine.cells import Cell
from donna.machine.records import RecordIndexItem, RecordKindItem
from donna.primitives.records import base


class PureText(RecordKindItem):
    kind: RecordKindId = RecordKindId("pure_text")  # TODO: kind must be defined in workflows?
    media_type: str
    content: str

    def cells(self, record: RecordIndexItem) -> list[Cell]:
        return [
            Cell.build(
                kind="pure_text_artifact",
                media_type=self.media_type,
                content=self.content,
                record_id=record.id,
                record_kind=self.kind,
                description=record.description,
            )
        ]


class PureTextKind(base.RecordKind):
    pass
