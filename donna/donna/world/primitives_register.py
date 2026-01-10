import importlib.util
import pathlib
import types
from typing import Any, Iterator, cast

from donna.domain.ids import NamespaceId
from donna.domain.types import RecordKindId
from donna.machine.artifacts import ArtifactKind
from donna.machine.operations import OperationKind
from donna.primitives.records.base import RecordKind
from donna.world.layout import layout
from donna.world.storage import Storage
from donna.machine.templates import RendererKind

BASE_WORKFLOWS_DIR = pathlib.Path(__file__).parent.parent / "workflows"


class PrimitivesRegister:

    def __init__(self) -> None:
        self.initialized = False
        self.operations: Storage[str, OperationKind] = Storage("operation")
        self.records: Storage[RecordKindId, RecordKind] = Storage("record_kind")
        self.artifacts: Storage[str, ArtifactKind] = Storage("artifact")
        self.renderers: Storage[str, RendererKind] = Storage("renderer")

    def _storages(self) -> Iterator[Storage[Any, Any]]:
        yield self.records
        yield self.artifacts

    def initialize(self) -> None:
        if self.initialized:
            return

        # TODO: this paths are not idiomatic anymore
        #       we should find a better way to organize code
        discover_operations(self, BASE_WORKFLOWS_DIR)
        discover_operations(self, layout().workflows)

        self.initialized = True

    def find_primitive(self, primitive_id: str) -> RecordKind | None:
        for storage in self._storages():
            primitive = storage.get(primitive_id)

            if primitive:
                return cast(RecordKind, primitive)

        return None

    def get_artifact_kind_by_namespace(self, namespace_id: NamespaceId) -> ArtifactKind | None:
        for kind in self.artifacts.values():
            if kind.namespace_id == namespace_id:
                return kind

        return None

    def register_module(self, module: types.ModuleType) -> None:
        for attr_name in dir(module):
            primitive = getattr(module, attr_name)

            if isinstance(primitive, ArtifactKind):
                self.artifacts.add(primitive)
                continue

            if isinstance(primitive, OperationKind):
                self.operations.add(primitive)
                continue

            if isinstance(primitive, RendererKind):
                self.renderers.add(primitive)
                continue


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

            if isinstance(attr, RecordKind):
                register.records.add(attr)
                continue
