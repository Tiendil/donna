import pathlib
import types
from typing import Any, Iterator, cast

from donna.domain.ids import ArtifactKindId, NamespaceId, OperationKindId, RendererKindId
from donna.machine.artifacts import ArtifactKind
from donna.machine.operations import OperationKind
from donna.machine.templates import RendererKind
from donna.world.storage import Storage

BASE_WORKFLOWS_DIR = pathlib.Path(__file__).parent.parent / "workflows"


class PrimitivesRegister:

    def __init__(self) -> None:
        self.operations: Storage[OperationKindId, OperationKind] = Storage("operation")
        self.artifacts: Storage[ArtifactKindId, ArtifactKind] = Storage("artifact")
        self.renderers: Storage[RendererKindId, RendererKind] = Storage("renderer")

    # TODO: what to do with that method?
    def _storages(self) -> Iterator[Storage[Any, Any]]:
        yield self.artifacts

    # TODO: what to do with that method?
    def find_primitive(self, primitive_id: ArtifactKindId) -> ArtifactKind | None:
        for storage in self._storages():
            primitive = storage.get(primitive_id)

            if primitive:
                return cast(ArtifactKind, primitive)

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

    return _REGISTER
