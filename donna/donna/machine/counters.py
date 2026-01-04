from typing import Callable

import pydantic

from donna.core.entities import BaseEntity
from donna.domain import types
from donna.world.layout import layout

_INTERNAL_COUNTERS: dict[Callable[[types.InternalId], types.InternalId], types.CounterId] = {
    types.WorkUnitId: types.CounterId("WU"),
    types.ActionRequestId: types.CounterId("AR"),
    types.TaskId: types.CounterId("T"),
    types.RecordId: types.CounterId("R"),
}


class Id(BaseEntity):
    id: types.CounterId
    value: int

    def to_int(self) -> int:
        return self.value

    def to_full(self) -> types.InternalId:
        return types.InternalId(f"{self.id}-{self.value}-{self.crc()}")

    def crc(self) -> str:
        """Translates int into a compact string representation with a-zA-Z0-9 characters."""
        charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        base = len(charset)

        num = self.value
        if num == 0:
            return charset[0]

        chars = []
        while num > 0:
            num, rem = divmod(num, base)
            chars.append(charset[rem])

        chars.reverse()
        return "".join(chars)


class Counters(BaseEntity):
    story_id: types.StoryId
    counters: dict[types.CounterId, int] = pydantic.Field(default_factory=dict)

    @classmethod
    def build(cls, story_id: types.StoryId) -> "Counters":
        return cls(story_id=story_id)

    @classmethod
    def load(cls, story_id: types.StoryId) -> "Counters":
        return cls.from_json(layout().story_counters(story_id).read_text())

    def save(self) -> None:
        layout().story_counters(self.story_id).write_text(self.to_json())

    def next(self, counter_id: types.CounterId) -> int:
        current_value = self.counters.get(counter_id, 1)

        next_value = current_value + 1

        self.counters[counter_id] = next_value

        return next_value

    def next_id(self, counter_id: types.CounterId) -> Id:
        next_value = self.next(counter_id)

        return Id(id=counter_id, value=next_value)


def next_id[InternalIdType: types.InternalId](
    story_id: types.StoryId,
    type_id: Callable[[types.InternalId], InternalIdType],
) -> InternalIdType:
    counters = Counters.load(story_id)

    if type_id not in _INTERNAL_COUNTERS:
        raise NotImplementedError(f"No counter defined for type '{type_id}'")

    counter_id = _INTERNAL_COUNTERS[type_id]

    next_id = counters.next_id(counter_id)

    counters.save()

    return type_id(next_id.to_full())


def create_id_parser[InternalIdType: types.InternalId](
    type_id: Callable[[types.InternalId], InternalIdType],
) -> Callable[[str], InternalIdType]:
    def parser(text: str) -> InternalIdType:
        parts = text.split("-")

        if len(parts) != 3:
            raise ValueError(f"Invalid id format: '{text}'")

        counter_id, number, crc = parts

        if counter_id not in _INTERNAL_COUNTERS.values():
            raise NotImplementedError(f"Unknown counter id: '{counter_id}'")

        id = Id(id=types.CounterId(counter_id), value=int(number))

        if id.crc() != crc:
            raise NotImplementedError(f"Invalid crc for id: '{text}'")

        return type_id(id.to_full())

    return parser
