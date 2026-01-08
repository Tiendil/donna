from typing import Any

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.types import RecordId, RecordKindId, StoryId
from donna.machine.cells import Cell
from donna.world.layout import layout


class RecordKind(BaseEntity):
    id: RecordKindId

    def save(self, story_id: StoryId, record_id: RecordId, item: "RecordKindItem") -> None:
        raise NotImplementedError("You must implement this method in subclasses")

    def load(self, story_id: StoryId, record_id: RecordId) -> "RecordKindItem":
        raise NotImplementedError("You must implement this method in subclasses")

    def remove(self, story_id: StoryId, record_id: RecordId) -> None:
        raise NotImplementedError("You must implement this method in subclasses")

    def specification(self) -> Any:
        raise NotImplementedError("You must implement this method in subclasses")

    def cells(self) -> list[Cell]:
        return [Cell.build_json(kind="record_kind_json_schema", content=self.specification(), record_kind=self.id)]


class RecordIndexItem(BaseEntity):
    id: RecordId
    kinds: list[RecordKindId]
    description: str

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)


class RecordKindSpec(BaseEntity):
    kind: RecordKindId

    @property
    def verbose(self) -> str:
        return f"<record kind: `{self.kind}`>"


class RecordKindItem(BaseEntity):
    kind: RecordKindId

    def cells(self, record: RecordIndexItem) -> list[Cell]:
        raise NotImplementedError("You must implement this method in subclasses")

    @classmethod
    def specification(cls) -> Any:
        return cls.model_json_schema()


class RecordsIndex(BaseEntity):
    story_id: StoryId
    records: list[RecordIndexItem]

    # TODO: we may want to make queue items frozen later
    model_config = pydantic.ConfigDict(frozen=False)

    def cells(self) -> list[Cell]:
        return [Cell.build_json(kind="records_index", content=self.model_dump(mode="json"))]

    @classmethod
    def load(cls, story_id: StoryId) -> "RecordsIndex":
        return cls.from_json(layout().story_records_index(story_id).read_text())

    def save(self) -> None:
        layout().story_records_index(self.story_id).write_text(self.to_json())

    def has_record(self, record_id: RecordId) -> bool:
        return any(record.id == record_id for record in self.records)

    def has_record_kind(self, record_id: RecordId, kind: RecordKindId) -> bool:
        if not self.has_record(record_id):
            return False

        item = self.get_record(record_id)

        assert item is not None

        return kind in item.kinds

    def get_record(self, record_id: RecordId) -> RecordIndexItem | None:
        for record in self.records:
            if record.id == record_id:
                return record

        return None

    def get_records_for_kind(self, kind: RecordKindId) -> list[RecordIndexItem]:
        result: list[RecordIndexItem] = []

        for record in self.records:
            if kind in record.kinds:
                result.append(record)

        return result

    def create_record(
        self,
        id: RecordId,
        description: str,
    ) -> None:
        if self.has_record(id):
            raise NotImplementedError(f"Record with id '{id}' already exists in story '{self.story_id}'")

        item = RecordIndexItem(id=id, kinds=[], description=description)

        self.records.append(item)

    def delete_record(self, record_id: RecordId) -> None:
        from donna.world.primitives_register import register

        item = self.get_record(record_id)

        if item is None:
            raise NotImplementedError(f"Record with id '{record_id}' does not exist in story '{self.story_id}'")

        for kind in item.kinds:
            record_kind = register().records.get(kind)
            assert record_kind is not None
            record_kind.remove(self.story_id, record_id)

        self.records = [record for record in self.records if record.id != record_id]

    def set_record_kind_item(self, record_id: RecordId, record_item: RecordKindItem) -> RecordKindItem:
        from donna.world.primitives_register import register

        item = self.get_record(record_id)

        if item is None:
            raise NotImplementedError(f"Record with id '{record_id}' does not exist in story '{self.story_id}'")

        if record_item.kind not in item.kinds:
            item.kinds.append(record_item.kind)

        record_kind = register().records.get(record_item.kind)
        assert record_kind is not None
        record_kind.save(self.story_id, record_id, record_item)

        return record_item

    def remove_record_kind_items(self, record_id: RecordId, kinds: list[RecordKindId]) -> None:
        from donna.world.primitives_register import register

        item = self.get_record(record_id)

        if item is None:
            raise NotImplementedError(f"Record with id '{record_id}' does not exist in story '{self.story_id}'")

        for kind in kinds:
            record_kind = register().records.get(kind)
            assert record_kind is not None
            record_kind.remove(self.story_id, record_id)

        item.kinds = [k for k in item.kinds if k not in kinds]

    def get_record_kind_items(self, record_id: RecordId, kinds: list[RecordKindId]) -> list[RecordKindItem | None]:
        from donna.world.primitives_register import register

        record = self.get_record(record_id)

        if record is None:
            raise NotImplementedError(f"Record with id '{record_id}' does not exist in story '{self.story_id}'")

        result: list[RecordKindItem | None] = []

        for kind in kinds:
            if kind not in record.kinds:
                result.append(None)
                continue

            record_kind = register().records.get(kind)
            assert record_kind is not None

            record_kind_item = record_kind.load(self.story_id, record_id)

            result.append(record_kind_item)

        return result
