import importlib.util
import pathlib
from typing import TYPE_CHECKING, Iterable, Iterator

from donna.agents.domain import ActionRequest, WorkflowCell
from donna.core.entities import BaseEntity
from donna.domain.layout import layout
from donna.domain.types import EventId, OperationId, OperationResultId
from donna.stories.events import Event, EventTemplate
from donna.workflows.tasks import Task, TaskState, WorkUnit

if TYPE_CHECKING:
    from donna.workflows.changes import Change


class Export(BaseEntity):
    name: str
    description: str


class OperationResult(BaseEntity):
    id: OperationResultId
    description: str
    event_id: EventId

    @classmethod
    def completed(cls, event_id: EventId) -> "OperationResult":
        return cls(
            id=OperationResultId("completed"),
            description="The action was completed successfully.",
            event_id=event_id,
        )


class Operation(BaseEntity):
    id: OperationId

    trigger_on: list[EventTemplate]

    results: list[OperationResult]

    export: Export | None = None

    def execute(self, task: Task, unit: WorkUnit) -> Iterable["Change"]:
        raise NotImplementedError("You MUST implement this method.")

    def result(self, id: OperationResultId) -> OperationResult:
        for result in self.results:
            if result.id == id:
                return result

        raise NotImplementedError(f"OperationResult with id '{id}' does not exist")


####################
# Operations storage
####################

# TODO: move them somewhere else

BASE_SCENARIOS_DIR = pathlib.Path(__file__).parent.parent / "scenarios"


class Storage:

    def __init__(self) -> None:
        self.initialized = False
        self._operations: dict[OperationId, Operation] = {}

    def initialize(self) -> None:
        if self.initialized:
            return

        discover_operations(self, BASE_SCENARIOS_DIR)
        discover_operations(self, layout().scenarios)

        self.initialized = True

    def add(self, operation: Operation) -> None:
        if operation.id in self._operations:
            raise NotImplementedError(f"Operation with id '{operation.id}' already exists")

        self._operations[operation.id] = operation

    def get(self, id: OperationId) -> Operation:
        if id not in self._operations:
            raise NotImplementedError(f"Operation with id '{id}' does not exist")

        return self._operations[id]

    def all(self) -> list[Operation]:
        return list(self._operations.values())

    def workflow_cells(self) -> list[WorkflowCell]:
        cells = [
            WorkflowCell(
                story_id=None,
                task_id=None,
                work_unit_id=None,
                workflow_id=operation.id,
                name=operation.export.name,
                description=operation.export.description,
            )
            for operation in self._operations.values()
            if operation.export is not None
        ]
        cells.sort(key=lambda c: c.name)
        return cells


_STORAGE: Storage | None = None


def storage() -> Storage:
    global _STORAGE

    if _STORAGE:
        return _STORAGE

    _STORAGE = Storage()
    _STORAGE.initialize()

    return _STORAGE


def discover_operations(storage: Storage, directory: pathlib.Path) -> None:  # noqa: CCR001
    """Discover all operations in the given directory

    - Recursively import all .py files in the given directory and try add operations from them
    - .py files processed in alphabetical order
    """
    for scenario_file in sorted(directory.rglob("*.py")):
        module_name = f"scenario_{id(scenario_file)}_{scenario_file.name.replace('.', '_')}"
        module_spec = importlib.util.spec_from_file_location(module_name, scenario_file)
        if module_spec is None or module_spec.loader is None:
            raise NotImplementedError(f"Cannot load scenario module from '{scenario_file}'")
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, Operation):
                storage.add(attr)


###################
# Operation helpers
###################

# TODO: move them somewhere else


class Simple(Operation):
    def execute(self, task: Task, unit: WorkUnit) -> Iterator["Change"]:
        from donna.workflows.changes import ChangeEvent

        yield ChangeEvent(Event.build(self.results[0].event_id, self.id, task.id))


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
        from donna.workflows.changes import ChangeAddActionRequest

        context = self.construct_context(task)

        request_text = self.request_template.format(**context)

        request = ActionRequest.build(task.story_id, request_text, self.id)
        yield ChangeAddActionRequest(request)


class FinishTask(Operation):
    def execute(self, task: Task, unit: WorkUnit) -> Iterator["Change"]:
        from donna.workflows.changes import ChangeTaskState

        yield ChangeTaskState(TaskState.COMPLETED)
