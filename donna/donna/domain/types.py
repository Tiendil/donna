import uuid
from typing import NewType

# Internal base types

CounterId = NewType("CounterId", str)
InternalId = NewType("InternalId", str)

# Ids that are integer-based with a prefix and CRC

WorkUnitId = NewType("WorkUnitId", InternalId)
ActionRequestId = NewType("ActionRequestId", InternalId)
TaskId = NewType("TaskId", InternalId)

# Ids that a pure string type

StoryId = NewType("StoryId", str)
OperationId = NewType("OperationId", str)

# Ids to refactor

RecordId = NewType("RecordId", str)
EventId = NewType("EventId", str)

RecordKindId = NewType("RecordKindId", str)
OperationResultId = NewType("OperationResultId", str)
RecordIdTemplate = NewType("RecordIdTemplate", str)
Slug = NewType("Slug", str)
SpecificationId = NewType("SpecificationId", str)
SpecificationSourceId = NewType("SpecificationSourceId", str)
