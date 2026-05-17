from typing import Any

import pydantic

from donna.core.entities import BaseEntity


class InternalError(Exception):
    message = "An internal error occurred"

    def __init__(self, **kwargs: Any) -> None:
        self.arguments = kwargs

    def error_message(self) -> str:
        return self.message.format(**self.arguments)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.error_message()}"


class EnvironmentError(BaseEntity):
    cell_kind: str
    cell_media_type: str = "text/markdown"

    code: str
    message: str
    ways_to_fix: list[str] = pydantic.Field(default_factory=list)

    def content_intro(self) -> str:
        return "Error"


class EnvironmentErrorsProxy(InternalError):
    message = "This is a technical exception to pass an environment error up the call stack."

    def __init__(self, errors: list[EnvironmentError]) -> None:
        super().__init__(errors=errors)


class CoreEnvironmentError(EnvironmentError):
    """Base class for environment errors in donna.core."""

    cell_kind: str = "core_environment_error"


ErrorsList = list[EnvironmentError]
