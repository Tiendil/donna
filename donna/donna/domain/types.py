from typing import NewType

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

# Ids that a pure slug type
# TODO: do we need Slug type?
# TODO: should we made Slug type a base type for the other Ids? with some validation
Slug = NewType("Slug", str)

StoryId = NewType("StoryId", str)
RecordKindId = NewType("RecordKindId", str)
OperationResultId = NewType("OperationResultId", str)
SpecificationSourceId = NewType("SpecificationSourceId", str)

# Nested Ids to organize static entities

EventId = NewType("EventId", NestedId)
OperationId = NewType("OperationId", NestedId)
SpecificationId = NewType("SpecificationId", NestedId)
