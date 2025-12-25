from typing import TYPE_CHECKING, Iterator

from donna.machine.operations import Operation
from donna.machine.tasks import Task, TaskState, WorkUnit

if TYPE_CHECKING:
    from donna.machine.changes import Change


class Finish(Operation):
    def execute(self, task: Task, unit: WorkUnit) -> Iterator["Change"]:
        from donna.machine.changes import ChangeTaskState

        yield ChangeTaskState(TaskState.COMPLETED)
