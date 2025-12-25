from typing import TYPE_CHECKING, Iterator

from donna.machine.events import Event
from donna.machine.tasks import Task, WorkUnit
from donna.machine.operations import Operation

if TYPE_CHECKING:
    from donna.machine.changes import Change


class Broadcast(Operation):
    def execute(self, task: Task, unit: WorkUnit) -> Iterator["Change"]:
        from donna.machine.changes import ChangeEvent

        for result in self.results:
            yield ChangeEvent(Event.build(result.event_id, self.id, task.id))
