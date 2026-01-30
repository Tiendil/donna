from donna.core import errors as core_errors


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.domain."""


class EnvironmentError(core_errors.EnvironmentError):
    """Base class for environment errors in donna.domain."""

    cell_kind: str = "domain_error"


class InvalidInternalId(InternalError):
    message: str = "Invalid InternalId: '{value}'."
    value: str


class InvalidIdentifier(InternalError):
    message: str = "Invalid identifier: '{value}'."
    value: str


class InvalidIdPath(InternalError):
    message: str = "Invalid {id_type}: '{value}'."
    id_type: str
    value: str


class InvalidIdFormat(EnvironmentError):
    code: str = "donna.domain.invalid_id_format"
    message: str = "Invalid {error.id_type}: '{error.value}'."
    ways_to_fix: list[str] = [
        "Ensure the value uses the expected format for {error.id_type}.",
    ]
    id_type: str
    value: str


class InvalidIdPattern(EnvironmentError):
    code: str = "donna.domain.invalid_id_pattern"
    message: str = "Invalid {error.id_type}: '{error.value}'."
    ways_to_fix: list[str] = [
        "Use identifiers or '*'/'**' tokens separated by the expected delimiter.",
    ]
    id_type: str
    value: str
