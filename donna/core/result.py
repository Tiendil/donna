from __future__ import annotations

import functools
from typing import Callable, Generic, ParamSpec, TypeVar, cast

from donna.core.errors import InternalError

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")
F = TypeVar("F")
P = ParamSpec("P")


class ResultError(InternalError):
    """Base class for internal errors in donna.core.result."""


class UnwrapError(ResultError):
    message: str = "Called unwrap on an Err value."


class UnwrapErrError(ResultError):
    message: str = "Called unwrap_err on an Ok value."


class Result(Generic[T, E]):
    __slots__ = ("_is_ok", "_value")

    def __init__(self, is_ok: bool, value: T | E) -> None:
        self._is_ok = is_ok
        self._value = value

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

        raise UnwrapError(error=self.unwrap_err())

    def unwrap_err(self) -> E:
        if not self._is_ok:
            return cast(E, self._value)

        raise UnwrapErrError(value=self.unwrap())

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


def unwrap_to_error(func: Callable[P, Result[T, E]]) -> Callable[P, Result[T, E]]:

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[T, E]:

        try:
            return func(*args, **kwargs)
        except UnwrapError as e:
            return Err(cast(E, e.arguments["error"]))

    return wrapper
