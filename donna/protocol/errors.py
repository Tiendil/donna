from typing import ClassVar

from llm_tool_cli.core.errors import EnvironmentError
from llm_tool_cli.protocol.logic_cells import EnvironmentErrorCell

from donna.core import errors as core_errors
from donna.protocol.nodes import Node


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.protocol."""


class ModeNotSet(InternalError):
    message_template: ClassVar[str] = "Mode is not set. Pass -p <mode> to the CLI."


class EnvironmentErrorNode(Node):
    __slots__ = ("_error",)

    def __init__(self, environment_error: EnvironmentError) -> None:
        self._error = environment_error

    def status(self) -> EnvironmentErrorCell:
        return EnvironmentErrorCell(error=self._error)

    def journal_message(self) -> str:
        return self._error.format_message().replace("\n", " ").strip()


def environment_error_node(error: EnvironmentError) -> EnvironmentErrorNode:
    return EnvironmentErrorNode(error)
