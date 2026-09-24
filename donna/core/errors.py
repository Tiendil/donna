from typing import ClassVar

from llm_tool_cli.core import errors as llm_tool_errors


class InternalError(llm_tool_errors.InternalError):
    message_template: ClassVar[str] = "An internal error occurred"


class EnvironmentError(llm_tool_errors.EnvironmentError):
    cell_kind: str
    cell_media_type: str = "text/markdown"

    def content_intro(self) -> str:
        return "Error"


class CoreEnvironmentError(EnvironmentError):
    """Base class for environment errors in donna.core."""

    cell_kind: str = "core_environment_error"
