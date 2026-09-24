from typing import ClassVar

from donna.core import errors as core_errors


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.domain."""


class EnvironmentError(core_errors.EnvironmentError):
    """Base class for environment errors in donna.domain."""

    cell_kind: str = "domain_error"


class InvalidInternalId(InternalError):
    message_template: ClassVar[str] = "Invalid InternalId: '{value}'."


class InvalidIdentifier(InternalError):
    message_template: ClassVar[str] = "Invalid identifier: '{value}'."


class InvalidIdPath(InternalError):
    message_template: ClassVar[str] = "Invalid {id_type}: '{value}'."


class InvalidIdFormat(EnvironmentError):
    code: str = "donna.domain.invalid_id_format"
    message: str = "Invalid {error.id_type}: '{error.value}'."
    ways_to_fix: list[str] = [
        "Ensure the value uses the expected format for {error.id_type}.",
    ]
    id_type: str
    value: str
