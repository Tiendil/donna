
from typing import TYPE_CHECKING, Iterable

from donna.core.entities import BaseEntity
from donna.domain.types import EventId, OperationId, OperationResultId, Slug, WorkflowId
from donna.machine.cells import Cell
from donna.machine.events import EventTemplate
from donna.machine.tasks import Task, WorkUnit


class Workflow(BaseEntity):
    id: WorkflowId
    operation_id: OperationId
    name: str
    description: str
