from donna.core import errors as core_errors


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.cli."""


class CliError(core_errors.EnvironmentError):
    cell_kind: str = "cli_error"


class InvalidSlugWithExtension(CliError):
    code: str = "donna.cli.invalid_slug_with_extension"
    message: str = "Invalid slug with extension: '{error.value}'."
    ways_to_fix: list[str] = [
        "Use the format '<slug>.<extension>' (for example: 'draft.md').",
    ]
    value: str
