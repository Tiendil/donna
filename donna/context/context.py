import contextvars

from donna.context.artifacts import ArtifactsCache
from donna.context.journal import Journal
from donna.context.output import NoopEmitter, OutputEmitter
from donna.context.primitives import PrimitivesCache
from donna.context.state import StateCache


class Context:
    __slots__ = (
        "_artifacts",
        "_state",
        "_primitives",
        "_journal",
        "output",
    )

    def __init__(self, output: OutputEmitter | None = None) -> None:
        self._artifacts = ArtifactsCache()
        self._state = StateCache()
        self._primitives = PrimitivesCache()
        self._journal = Journal(self)
        self.output = output if output is not None else NoopEmitter()

    @property
    def artifacts(self) -> ArtifactsCache:
        return self._artifacts

    @property
    def state(self) -> StateCache:
        return self._state

    @property
    def primitives(self) -> PrimitivesCache:
        return self._primitives

    @property
    def journal(self) -> Journal:
        return self._journal


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
