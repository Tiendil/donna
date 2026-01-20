import pathlib
import types

from donna.domain.ids import DirectiveKindId
from donna.machine.templates import DirectiveKind
from donna.world.storage import Storage

BASE_WORKFLOWS_DIR = pathlib.Path(__file__).parent.parent / "workflows"


class PrimitivesRegister:

    def __init__(self) -> None:
        self.directives: Storage[DirectiveKindId, DirectiveKind] = Storage("directive")

    def register_module(self, module: types.ModuleType) -> None:
        for attr_name in dir(module):
            primitive = getattr(module, attr_name)

            if isinstance(primitive, DirectiveKind):
                self.directives.add(primitive)
                continue


_REGISTER: PrimitivesRegister | None = None


def register() -> PrimitivesRegister:
    global _REGISTER

    if _REGISTER:
        return _REGISTER

    _REGISTER = PrimitivesRegister()

    return _REGISTER
