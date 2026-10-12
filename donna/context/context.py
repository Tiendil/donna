import contextvars

from donna.context.journal import Journal


class Context:
    __slots__ = ("_journal",)

    def __init__(self) -> None:
        self._journal = Journal()

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
