import uuid
from typing import NewType

StoryId = NewType("StoryId", str)
WorkUnitId = NewType("WorkUnitId", uuid.UUID)
RecordId = NewType("RecordId", str)
ActionRequestId = NewType("ActionRequestId", uuid.UUID)
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


def new_work_unit_id() -> WorkUnitId:
    return WorkUnitId(uuid.uuid4())


def new_action_request_id() -> ActionRequestId:
    return ActionRequestId(uuid.uuid4())


def str_to_action_request_id(text: str) -> ActionRequestId:
    return ActionRequestId(uuid.UUID(text))
