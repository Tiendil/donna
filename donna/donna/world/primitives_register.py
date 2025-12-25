import importlib.util
import pathlib

from donna.domain.types import OperationId
from donna.machine.operations import Operation
from donna.world.layout import layout
from donna.world.storage import Storage

BASE_BEHAVIORS_DIR = pathlib.Path(__file__).parent.parent / "behaviors"


class PrimitivesRegister:

    def __init__(self) -> None:
        self.initialized = False
        self.operations: Storage[OperationId, Operation] = Storage("operation")

    def initialize(self) -> None:
        if self.initialized:
            return

        # TODO: this paths are not idiomatic anymore
        #       we should find a better way to organize code
        discover_operations(self, BASE_BEHAVIORS_DIR)
        discover_operations(self, layout().behaviors)

        self.initialized = True


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
    for behavior_file in sorted(directory.rglob("*.py")):
        module_name = f"donna_import_{id(behavior_file)}_{behavior_file.name.replace('.', '_')}"
        module_spec = importlib.util.spec_from_file_location(module_name, behavior_file)

        if module_spec is None or module_spec.loader is None:
            raise NotImplementedError(f"Cannot load behavior module from '{behavior_file}'")

        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if isinstance(attr, Operation):
                register.operations.add(attr)
