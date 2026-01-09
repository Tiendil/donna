import pydantic

from donna.core.entities import BaseEntity
from donna.domain import types
from donna.world.layout import layout


class Counters(BaseEntity):
    counters: dict[types.CounterId, int] = pydantic.Field(default_factory=dict)

    @classmethod
    def build(cls) -> "Counters":
        return cls()

    @classmethod
    def load(cls) -> "Counters":
        return cls.from_json(layout().session_counters().read_text())

    def save(self) -> None:
        layout().session_counters().write_text(self.to_json())

    def next(self, counter_id: types.CounterId) -> int:
        current_value = self.counters.get(counter_id, 1)

        next_value = current_value + 1

        self.counters[counter_id] = next_value

        return next_value
