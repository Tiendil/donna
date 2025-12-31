from typing import TYPE_CHECKING, Iterator

from donna.machine.action_requests import ActionRequest
from donna.machine.operations import Operation
from donna.machine.tasks import Task, WorkUnit
from donna.machine.records import RecordKindSpec
from donna.machine.cells import Cell

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

    def reminders(self) -> Iterator[Cell]:
        for record_kind_spec in dir(self):
            value = getattr(self, record_kind_spec)

            if not isinstance(value, RecordKindSpec):
                continue

            yield from value.cells()

    def execute(self, task: Task, unit: WorkUnit) -> Iterator["Change"]:
        from donna.machine.changes import ChangeAddActionRequest

        context = self.construct_context(task)

        request_text = self.request_template.format(**context)

        request = ActionRequest.build(task.story_id, request_text, self.id, reminders=list(self.reminders()))
        yield ChangeAddActionRequest(request)
