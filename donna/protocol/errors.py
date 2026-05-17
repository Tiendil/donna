from donna.core import errors as core_errors
from donna.protocol.cells import Cell, MetaValue, to_meta_value
from donna.protocol.nodes import Node


class InternalError(core_errors.InternalError):
    """Base class for internal errors in donna.protocol."""


class ModeNotSet(InternalError):
    message: str = "Mode is not set. Pass -p <mode> to the CLI."


class UnsupportedFormatterMode(InternalError):
    message: str = "Formatter for mode '{mode}' is not implemented."


class ContentWithoutMediaType(InternalError):
    message: str = "Cannot set content when media_type is None."


class EnvironmentErrorNode(Node):
    __slots__ = ("_error",)

    def __init__(self, environment_error: core_errors.EnvironmentError) -> None:
        self._error = environment_error

    def meta(self) -> dict[str, MetaValue]:
        meta: dict[str, MetaValue] = {
            "error_code": self._error.code,
        }

        for field_name, _field in self._error.model_fields.items():
            if field_name in ("code", "message", "cell_kind", "cell_media_type", "ways_to_fix"):
                continue

            value = getattr(self._error, field_name)

            if value is None:
                continue

            meta[field_name] = to_meta_value(value)

        return meta

    def content(self) -> str:
        intro = self._error.content_intro()

        message = self._error.message.format(error=self._error).strip()

        ways_to_fix = [fix.format(error=self._error).strip() for fix in self._error.ways_to_fix]

        if "\n" in self._error.message:
            content = f"{intro}:\n\n{message}"
        else:
            content = f"{intro}: {message}"

        if not ways_to_fix:
            return content

        if len(ways_to_fix) == 1:
            return f"{content}\nWay to fix: {ways_to_fix[0]}"

        fixes = "\n".join(f"- {fix}" for fix in ways_to_fix)

        return f"{content}\n\nWays to fix:\n\n{fixes}"

    def status(self) -> Cell:
        return Cell.build(
            kind=self._error.cell_kind,
            media_type=self._error.cell_media_type,
            content=self.content(),
            **self.meta(),
        )

    def journal_message(self) -> str:
        return self._error.message.format(error=self._error).replace("\n", " ").strip()


def environment_error_node(error: core_errors.EnvironmentError) -> EnvironmentErrorNode:
    return EnvironmentErrorNode(error)
