from typing import Any

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.types import EventId, OperationId, TaskId


# TODO: in the future we may want a strict control on event parameter types
#       => we may want to add EventScema entity to the register
#          and validate against it at event & event template creation time
#       however for now we keep it simple, because:
#       - it is easy & faster to implement
#       - there is no end vision yet on how events should work


EventAgrument = int | None | str


class Event(BaseEntity):
    id: EventId
    arguments: dict[str, str]

    @classmethod
    def build(cls, id: EventId, **kwargs: EventAgrument) -> "Event":
        return Event(
            id=id,
            arguments=kwargs,
        )


class EventTemplate(BaseEntity):
    id: EventId
    # TODO: we may want to add variables here to capture dynamic parts of the event id
    arguments: dict[str, str]

    @classmethod
    def build(cls, id: EventId, **kwargs: EventAgrument) -> "EventTemplate":
        return EventTemplate(
            id=id,
            arguments=kwargs,
        )

    def match(self, event: Event) -> bool:
        if self.id != event.id:
            return False

        for key, value in self.arguments.items():
            if key not in event.arguments:
                return False

            if event.arguments[key] != value:
                return False

        return True
