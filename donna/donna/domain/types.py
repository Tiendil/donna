import uuid
from typing import NewType

StoryId = NewType("StoryId", str)
CounterId = NewType("CounterId", str)
InternalId = NewType("InternalId", str)

WorkUnitId = NewType("WorkUnitId", InternalId)
ActionRequestId = NewType("ActionRequestId", InternalId)

RecordId = NewType("RecordId", str)
EventId = NewType("EventId", str)
OperationId = NewType("OperationId", str)
RecordKindId = NewType("RecordKindId", str)
TaskId = NewType("TaskId", uuid.UUID)
OperationResultId = NewType("OperationResultId", str)
RecordIdTemplate = NewType("RecordIdTemplate", str)
Slug = NewType("Slug", str)
SpecificationId = NewType("SpecificationId", str)
SpecificationSourceId = NewType("SpecificationSourceId", str)


def new_task_id() -> TaskId:
    return TaskId(uuid.uuid4())
