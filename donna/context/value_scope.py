from collections.abc import Iterator
from contextlib import contextmanager
from typing import Generic, TypeVar

V = TypeVar("V")


class ValueScope(Generic[V]):
    __slots__ = ("_value",)

    def __init__(self, initial: V | None = None) -> None:
        self._value: V | None = initial

    def get(self) -> V | None:
        return self._value

    @contextmanager
    def scope(self, value: V | None) -> Iterator[None]:
        previous = self._value
        self._value = value
        try:
            yield
        finally:
            self._value = previous
