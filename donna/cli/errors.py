from donna.core import errors as core_errors


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.cli."""


class CliError(core_errors.EnvironmentError):
    cell_kind: str = "cli_error"
