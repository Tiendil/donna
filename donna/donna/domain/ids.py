from donna.domain import types
from typing import Callable


_STORY_COUNTERS: dict[Callable[[types.InternalId], types.InternalId], types.CounterId] = {
    types.WorkUnitId: types.CounterId("WU"),
    types.ActionRequestId: types.CounterId("AR"),
    types.TaskId: types.CounterId("T"),
    types.RecordId: types.CounterId("R"),
}


class RichInternalId:
    __slots__ = ("id", "value")

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


def next_id[InternalIdType: types.InternalId](
    story_id: types.StoryId,
    type_id: Callable[[types.InternalId], InternalIdType],
) -> InternalIdType:
    # TODO: the direction of this dependency is wrong (`domain` should not depend on `machine`).
    #       It is acceptable on the early stages of development, but should be fixed later.
    from donna.machine.counters import Counters

    counters = Counters.load(story_id)

    if type_id not in _STORY_COUNTERS:
        raise NotImplementedError(f"No counter defined for type '{type_id}'")

    counter_id = _STORY_COUNTERS[type_id]

    next_id = counters.next(counter_id)

    counters.save()

    id = RichInternalId(id=counter_id, value=next_id)

    return type_id(id.to_full())


def create_id_parser[InternalIdType: types.InternalId](
    type_id: Callable[[types.InternalId], InternalIdType],
) -> Callable[[str], InternalIdType]:
    def parser(text: str) -> InternalIdType:
        parts = text.split("-")

        if len(parts) != 3:
            raise ValueError(f"Invalid id format: '{text}'")

        counter_id, number, crc = parts

        if counter_id not in _STORY_COUNTERS.values():
            raise NotImplementedError(f"Unknown counter id: '{counter_id}'")

        id = RichInternalId(id=types.CounterId(counter_id), value=int(number))

        if id.crc() != crc:
            raise NotImplementedError(f"Invalid crc for id: '{text}'")

        return type_id(id.to_full())

    return parser
