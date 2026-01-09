from typing import Any

from donna.domain.types import RecordId
from donna.machine.records import RecordKind as BaseRecordKind
from donna.machine.records import RecordKindItem
from donna.world.layout import layout


class RecordKind(BaseRecordKind):
    item_class: type[RecordKindItem]

    def save(self, record_id: RecordId, item: RecordKindItem) -> None:
        path = layout().session_record_kind(record_id, item.kind)

        with path.open("w", encoding="utf-8") as f:
            content = item.to_json()
            f.write(content)

    def load(self, record_id: RecordId) -> RecordKindItem:
        path = layout().session_record_kind(record_id, self.id)

        if not path.exists():
            raise NotImplementedError(
                f"Record kind '{self.id}' for record '{record_id}' does not exist in session"
            )

        with path.open("r", encoding="utf-8") as f:
            content = f.read()

        item = self.item_class.from_json(content)

        return item

    def remove(self, record_id: RecordId) -> None:
        path = layout().session_record_kind(record_id, self.id)

        if path.exists():
            path.unlink()

    def specification(self) -> Any:
        return self.item_class.specification()
