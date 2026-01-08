import importlib.util
import pathlib
from typing import Any, Iterator, cast

from donna.domain.types import OperationId, RecordKindId, WorkflowId
from donna.machine.operations import Operation
from donna.machine.workflows import Workflow
from donna.primitives.records.base import RecordKind
from donna.world.layout import layout
from donna.world.storage import Storage

BASE_WORKFLOWS_DIR = pathlib.Path(__file__).parent.parent / "workflows"


class PrimitivesRegister:

    def __init__(self) -> None:
        self.initialized = False
        self.operations: Storage[OperationId, Operation] = Storage("operation")
        self.records: Storage[RecordKindId, RecordKind] = Storage("record_kind")
        self.workflows: Storage[WorkflowId, Workflow] = Storage("workflow")

    def _storages(self) -> Iterator[Storage[Any, Any]]:
        yield self.operations
        yield self.records
        yield self.workflows

    def initialize(self) -> None:
        if self.initialized:
            return

        # TODO: this paths are not idiomatic anymore
        #       we should find a better way to organize code
        discover_operations(self, BASE_WORKFLOWS_DIR)
        discover_operations(self, layout().workflows)

        self.initialized = True

    def find_primitive(self, primitive_id: str) -> Operation | RecordKind | Workflow | None:
        for storage in self._storages():
            primitive = storage.get(primitive_id)

            if primitive:
                return cast(Operation | RecordKind | Workflow, primitive)

        return None


_REGISTER: PrimitivesRegister | None = None


def register() -> PrimitivesRegister:
    global _REGISTER

    if _REGISTER:
        return _REGISTER

    _REGISTER = PrimitivesRegister()
    _REGISTER.initialize()

    return _REGISTER


def discover_operations(register: PrimitivesRegister, directory: pathlib.Path) -> None:  # noqa: CCR001
    """Discover all operations in the given directory

    - Recursively import all .py files in the given directory and try add operations from them
    - .py files processed in alphabetical order
    """
    for workflow_file in sorted(directory.rglob("*.py")):
        module_name = f"donna_import_{id(workflow_file)}_{workflow_file.name.replace('.', '_')}"
        module_spec = importlib.util.spec_from_file_location(module_name, workflow_file)

        if module_spec is None or module_spec.loader is None:
            raise NotImplementedError(f"Cannot load workflow module from '{workflow_file}'")

        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if isinstance(attr, Operation):
                register.operations.add(attr)
                continue

            if isinstance(attr, RecordKind):
                register.records.add(attr)
                continue

            if isinstance(attr, Workflow):
                register.workflows.add(attr)
                continue
