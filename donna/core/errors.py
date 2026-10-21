from typing import ClassVar

from llm_tool_cli.core import errors as llm_tool_errors


class InternalError(llm_tool_errors.InternalError):
    message_template: ClassVar[str] = "An internal error occurred"


class EnvironmentError(llm_tool_errors.EnvironmentError):
    """Base class for Donna-owned operational failures."""


class CoreEnvironmentError(EnvironmentError):
    """Base class for environment errors in donna.core."""
