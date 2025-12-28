import pathlib
import shutil

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.types import RecordId, RecordKindId, StoryId
from donna.machine.cells import AgentCellHistory
from donna.world.layout import layout


class RecordKind(BaseEntity):
    id: RecordKindId

    def save(self, story_id: StoryId, record_id: RecordId, item: "RecordKindItem") -> None:
        raise NotImplementedError("You must implement this method in subclasses")

    def load(self, story_id: StoryId, record_id: RecordId) -> "RecordKindItem":
        raise NotImplementedError("You must implement this method in subclasses")

    def remove(self, story_id: StoryId, record_id: RecordId) -> None:
        raise NotImplementedError("You must implement this method in subclasses")


class RecordIndexItem(BaseEntity):
    id: RecordId
    kinds: list[RecordKindId]
    description: str


class RecordKindItem(BaseEntity):
    kind: RecordKindId
    # story_id: StoryId

    def cells(self, record: RecordIndexItem) -> list[AgentCellHistory]:
        raise NotImplementedError("You must implement this method in subclasses")


class RecordsIndex(BaseEntity):
    story_id: StoryId
    records: list[RecordIndexItem]

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)

    def cells(self) -> list[AgentCellHistory]:
        return [AgentCellHistory(work_unit_id=None, body=self.to_toml())]

    @classmethod
    def load(cls, story_id: StoryId) -> "RecordsIndex":
        return cls.from_toml(layout().story_records_index(story_id).read_text())

    def save(self) -> None:
        layout().story_records_index(self.story_id).write_text(self.to_toml())

    def has_record(self, record_id: RecordId) -> bool:
        return any(record.id == record_id for record in self.records)

    def get_record(self, record_id: RecordId) -> RecordIndexItem | None:
        for record in self.records:
            if record.id == record_id:
                return record

        return None

    def create_record(
        self,
        id: RecordId,
        description: str,
    ) -> None:
        if self.has(id):
            raise NotImplementedError(f"Record with id '{id}' already exists in story '{self.story_id}'")

        item = RecordIndexItem(id=id, kinds=[], description=description)

        self.records.append(item)

        # self.record_path(id).touch()

    # def record_path(self, record_id: RecordId) -> pathlib.Path:
    #     if not self.has(record_id):
    #         raise NotImplementedError(f"Record with id '{record_id}' does not exist in story '{self.story_id}'")

    #     return layout().story_record(self.story_id, record_id)

    def delete_record(self, record_id: RecordId) -> None:
        from donna.world.primitives_register import register

        item = self.get_record(record_id)

        for kind in item.kinds:
            register().records.get(kind).remove(self.story_id, record_id)

        self.records = [record for record in self.records if record.id != record_id]
        # path.unlink()

    def set_record_kind_item(self, record_id: RecordId, item: RecordKind) -> RecordKindItem:
        from donna.world.primitives_register import register

        item = self.get(record_id)

        if item is None:
            raise NotImplementedError(f"Record with id '{record_id}' does not exist in story '{self.story_id}'")

        if item.kind not in item.kinds:
            item.kinds.append(item.kind)

        register().records.get(item.kind).save(self.story_id, record_id, item)

        # with self.record_kind_path(record_id, item.kind).open("w", encoding="utf-8") as f:
        #     content = item.to_toml()
        #     f.write(content)

    def remove_record_kind_items(self, record_id: RecordId, kinds: list[RecordKindId]) -> None:
        from donna.world.primitives_register import register

        item = self.get(record_id)

        if item is None:
            raise NotImplementedError(f"Record with id '{record_id}' does not exist in story '{self.story_id}'")

        for kind in kinds:
            register().records.get(kind).remove(self.story_id, record_id)

        item.kinds = [k for k in item.kinds if k not in kinds]

    def get_record_kind_items(self, record_id: RecordId, kinds: list[RecordKindId]) -> list[RecordKindItem]:
        from donna.world.primitives_register import register

        item = self.get(record_id)

        if item is None:
            raise NotImplementedError(f"Record with id '{record_id}' does not exist in story '{self.story_id}'")

        result: list[RecordKindItem] = []

        for kind in kinds:
            if kind not in item.kinds:
                result.append(None)
                continue

            record_kind = register().records.get(kind)

            item = record_kind.load(self.story_id, record_id)

            result.append(item)
