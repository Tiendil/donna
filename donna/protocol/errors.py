from typing import ClassVar

from donna.core import errors as core_errors


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.protocol."""


class ModeNotSet(InternalError):
    message_template: ClassVar[str] = "Mode is not set. Pass -p <mode> to the CLI."
