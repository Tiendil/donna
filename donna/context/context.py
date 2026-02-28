import contextvars

from donna.context.artifacts import ArtifactsCache
from donna.context.primitives import PrimitivesCache
from donna.context.state import StateCache
from donna.context.value_scope import ValueScope
from donna.domain.ids import FullArtifactSectionId, WorkUnitId


class Context:
    __slots__ = (
        "_artifacts",
        "_state",
        "_primitives",
        "current_work_unit_id",
        "current_operation_id",
    )

    def __init__(self) -> None:
        self._artifacts = ArtifactsCache()
        self._state = StateCache()
        self._primitives = PrimitivesCache()
        self.current_work_unit_id: ValueScope[WorkUnitId] = ValueScope()
        self.current_operation_id: ValueScope[FullArtifactSectionId] = ValueScope()

    @property
    def artifacts(self) -> ArtifactsCache:
        return self._artifacts

    @property
    def state(self) -> StateCache:
        return self._state

    @property
    def primitives(self) -> PrimitivesCache:
        return self._primitives


_context_var: contextvars.ContextVar[Context | None] = contextvars.ContextVar("donna_machine_context", default=None)


def set_context(new_context: Context) -> contextvars.Token[Context | None]:
    return _context_var.set(new_context)


def reset_context(token: contextvars.Token[Context | None]) -> None:
    _context_var.reset(token)


def context() -> Context:
    current = _context_var.get()
    if current is None:
        raise RuntimeError("Donna machine context is not initialized")

    return current
