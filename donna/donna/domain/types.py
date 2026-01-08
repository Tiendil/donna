from typing import Callable, NewType

# Internal base types

CounterId = NewType("CounterId", str)
InternalId = NewType("InternalId", str)
NestedId = NewType("NestedId", str)

# Ids that are integer-based with a prefix and CRC
# I.e. dynamically generated ids

WorkUnitId = NewType("WorkUnitId", InternalId)
ActionRequestId = NewType("ActionRequestId", InternalId)
TaskId = NewType("TaskId", InternalId)
RecordId = NewType("RecordId", InternalId)

# Ids that are lowercase ASCII without spaces

Slug = NewType("Slug", str)

WorldId = NewType("WorldId", Slug)
StoryId = NewType("StoryId", Slug)
RecordKindId = NewType("RecordKindId", Slug)
OperationResultId = NewType("OperationResultId", Slug)
SpecificationSourceId = NewType("SpecificationSourceId", Slug)

# Nested Ids to organize static entities

EventId = NewType("EventId", NestedId)
OperationId = NewType("OperationId", NestedId)
SpecificationId = NewType("SpecificationId", NestedId)
WorkflowId = NewType("WorkflowId", NestedId)


def slug_parser(text: str) -> Slug:
    allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789-_"

    if not all(c in allowed_chars for c in text):
        raise ValueError(f"Invalid slug '{text}'. Allowed characters are: {allowed_chars}")

    return Slug(text)


def child_slug_parser[T: Slug](type_id: Callable[[Slug], T]) -> Callable[[str], T]:
    def parser(text: str) -> T:
        return type_id(slug_parser(text))

    return parser
