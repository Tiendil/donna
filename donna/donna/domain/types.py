import uuid
from typing import NewType

StoryId = NewType("StoryId", str)
CounterId = NewType("CounterId", str)
InternalId = NewType("InternalId", str)

WorkUnitId = NewType("WorkUnitId", InternalId)
ActionRequestId = NewType("ActionRequestId", InternalId)
TaskId = NewType("TaskId", InternalId)

RecordId = NewType("RecordId", str)
EventId = NewType("EventId", str)
OperationId = NewType("OperationId", str)
RecordKindId = NewType("RecordKindId", str)
OperationResultId = NewType("OperationResultId", str)
RecordIdTemplate = NewType("RecordIdTemplate", str)
Slug = NewType("Slug", str)
SpecificationId = NewType("SpecificationId", str)
SpecificationSourceId = NewType("SpecificationSourceId", str)
