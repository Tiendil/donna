from typing import Callable

import pydantic

from donna.core.entities import BaseEntity
from donna.domain import types
from donna.world.layout import layout


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
