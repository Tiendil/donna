from donna.core import errors as core_errors


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.protocol."""


class ModeNotSet(InternalError):
    message: str = "Mode is not set. Pass -p <mode> to the CLI."


class UnsupportedFormatterMode(InternalError):
    message: str = "Formatter for mode '{mode}' is not implemented."


class ContentWithoutMediaType(InternalError):
    message: str = "Cannot set content when media_type is None."
