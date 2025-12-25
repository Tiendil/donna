from typing import Any

import pydantic

from donna.core.entities import BaseEntity
from donna.domain.types import EventId, OperationId, TaskId


class Event(BaseEntity):
    id: EventId
    operation_id: OperationId
    task_id: TaskId

    @classmethod
    def build(cls, id: EventId, operation_id: OperationId, task_id: TaskId) -> "Event":
        return Event(
            id=id,
            operation_id=operation_id,
            task_id=task_id,
        )


class EventTemplate(BaseEntity):
    id: EventId | None
    operation_id: OperationId | None

    def match(self, event: Event) -> bool:
        if self.id is not None and self.id != event.id:
            return False

        if self.operation_id is not None and self.operation_id != event.operation_id:
            return False

        return True

    @pydantic.model_validator(mode="before")
    @classmethod
    def _coerce_from_scalar(cls, value: Any) -> Any:
        if isinstance(value, cls):
            return value

        if isinstance(value, str):
            return {"id": value, "operation_id": None}

        return value
