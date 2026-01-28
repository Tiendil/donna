from typing import Any

import pydantic

from donna.core.entities import BaseEntity
from donna.protocol.cells import Cell, MetaValue, to_meta_value
from donna.protocol.nodes import Node


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

    def node(self) -> "EnvironmentErrorNode":
        return EnvironmentErrorNode(self)


class EnvironmentErrorNode(Node):
    __slots__ = ("_error",)

    def __init__(self, environment_error: EnvironmentError) -> None:
        self._error = environment_error

    def meta(self) -> dict[str, MetaValue]:
        meta: dict[str, MetaValue] = {
            "error_code": self._error.code,
        }

        for field_name, _field in self._error.model_fields.items():
            if field_name in ("code", "message", "cell_kind"):
                continue

            value = getattr(self, field_name)

            if value is None:
                continue

            meta[field_name] = to_meta_value(value)

        return meta

    def content(self) -> str:
        intro = self._error.content_intro()

        message = self._error.message.format(error=self).strip()

        if "\n" in self._error.message:
            content = f"{intro}:\n\n{message}"
        else:
            content = f"{intro}: {message}"

        if not self._error.ways_to_fix:
            return content

        if len(self._error.ways_to_fix) == 1:
            return f"{content}\nWay to fix: {self._error.ways_to_fix[0]}"

        fixes = "\n".join(f"- {fix}" for fix in self._error.ways_to_fix)

        return f"{content}\n\nWays to fix:\n\n{fixes}"

    def status(self) -> Cell:
        return Cell.build(
            kind=self._error.cell_kind,
            media_type=self._error.cell_media_type,
            content=self.content(),
            **self.meta(),
        )


ErrorsList = list[EnvironmentError]
