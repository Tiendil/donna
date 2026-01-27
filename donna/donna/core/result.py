from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, cast

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")
F = TypeVar("F")


@dataclass(frozen=True, slots=True)
class Result(Generic[T, E]):
    _is_ok: bool
    _value: object

    def is_ok(self) -> bool:
        return self._is_ok

    def is_err(self) -> bool:
        return not self._is_ok

    def ok(self) -> T | None:
        if self._is_ok:
            return cast(T, self._value)
        return None

    def err(self) -> E | None:
        if not self._is_ok:
            return cast(E, self._value)
        return None

    def unwrap(self) -> T:
        if self._is_ok:
            return cast(T, self._value)
        raise ValueError("Called unwrap on an Err value.")

    def unwrap_err(self) -> E:
        if not self._is_ok:
            return cast(E, self._value)
        raise ValueError("Called unwrap_err on an Ok value.")

    def unwrap_or(self, default: U) -> T | U:
        if self._is_ok:
            return cast(T, self._value)
        return default

    def map(self, func: Callable[[T], U]) -> "Result[U, E]":
        if self._is_ok:
            return Result(True, func(cast(T, self._value)))
        return Result(False, cast(E, self._value))

    def map_err(self, func: Callable[[E], F]) -> "Result[T, F]":
        if not self._is_ok:
            return Result(False, func(cast(E, self._value)))
        return Result(True, cast(T, self._value))


def Ok(value: T) -> Result[T, E]:
    return Result(True, value)


def Err(error: E) -> Result[T, E]:
    return Result(False, error)


def ok(result: Result[T, E]) -> bool:
    return result.is_ok()
