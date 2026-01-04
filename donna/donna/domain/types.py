import uuid
from typing import NewType

# Internal base types

CounterId = NewType("CounterId", str)
InternalId = NewType("InternalId", str)

# Ids that are integer-based with a prefix and CRC
# I.e. dynamically generated ids

WorkUnitId = NewType("WorkUnitId", InternalId)
ActionRequestId = NewType("ActionRequestId", InternalId)
TaskId = NewType("TaskId", InternalId)

# Ids that a pure slug type
# TODO: do we need Slug type?
# TODO: should we made Slug type a base type for the other Ids? with some validation
Slug = NewType("Slug", str)

StoryId = NewType("StoryId", str)
RecordKindId = NewType("RecordKindId", str)
OperationResultId = NewType("OperationResultId", str)
SpecificationSourceId = NewType("SpecificationSourceId", str)

# Ids that a more complex string type
# TODO: also refactor?

EventId = NewType("EventId", str)
OperationId = NewType("OperationId", str)
# TODO: we may want to refactor this into dynamic id with optional slug
# TODO: at lease we may want to replace `/` with `:`
SpecificationId = NewType("SpecificationId", str)


# Ids to refactor

RecordId = NewType("RecordId", str)

RecordIdTemplate = NewType("RecordIdTemplate", str)
