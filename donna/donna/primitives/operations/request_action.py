import importlib.util
import pathlib
from typing import TYPE_CHECKING, Iterable, Iterator

from donna.machine.action_requests import ActionRequest
from donna.machine.cells import WorkflowCell
from donna.core.entities import BaseEntity
from donna.world.layout import layout
from donna.domain.types import EventId, OperationId, OperationResultId
from donna.machine.events import Event, EventTemplate
from donna.machine.tasks import Task, TaskState, WorkUnit
from donna.machine.operations import Operation

if TYPE_CHECKING:
    from donna.machine.changes import Change


class RequestAction(Operation):
    request_template: str

    def construct_context(self, task: Task) -> dict[str, object]:
        context: dict[str, object] = {}

        for method_name in dir(self):
            if not method_name.startswith("context_"):
                continue

            name = method_name[len("context_") :]
            value = getattr(self, method_name)(task)

            if value is None:
                continue

            context[name] = value

        context["scheme"] = self

        return context

    def execute(self, task: Task, unit: WorkUnit) -> Iterator["Change"]:
        from donna.machine.changes import ChangeAddActionRequest

        context = self.construct_context(task)

        request_text = self.request_template.format(**context)

        request = ActionRequest.build(task.story_id, request_text, self.id)
        yield ChangeAddActionRequest(request)
