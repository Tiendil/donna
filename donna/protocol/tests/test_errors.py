from decimal import Decimal

from donna.core import errors as core_errors
from donna.protocol.errors import EnvironmentErrorNode, environment_error_node


class _SingleFixError(core_errors.EnvironmentError):
    cell_kind: str = "sample_error"
    code: str = "sample.single"
    message: str = "Problem with {error.item}."
    ways_to_fix: list[str] = ["Fix {error.item}."]
    item: str
    count: int
    active: bool
    optional: str | None = None
    decimal_value: Decimal

    def content_intro(self) -> str:
        return "Sample"


class _MultipleFixesError(core_errors.EnvironmentError):
    cell_kind: str = "sample_error"
    code: str = "sample.multiple"
    message: str = "Problem with {error.item}."
    ways_to_fix: list[str] = ["Fix {error.item}.", "Retry."]
    item: str


class _MultilineError(core_errors.EnvironmentError):
    cell_kind: str = "sample_error"
    code: str = "sample.multiline"
    message: str = "First line.\nSecond line."


class TestEnvironmentErrorNode:
    def test_meta__includes_code_and_scalar_context_fields(self) -> None:
        node = EnvironmentErrorNode(
            _SingleFixError(item="artifact", count=3, active=True, decimal_value=Decimal("1.5"))
        )

        assert node.meta() == {
            "error_code": "sample.single",
            "item": "artifact",
            "count": 3,
            "active": True,
            "decimal_value": "1.5",
        }

    def test_content__renders_single_fix(self) -> None:
        node = EnvironmentErrorNode(
            _SingleFixError(item="artifact", count=3, active=True, decimal_value=Decimal("1.5"))
        )

        assert node.content() == "Sample: Problem with artifact.\nWay to fix: Fix artifact."

    def test_content__renders_multiple_fixes_as_list(self) -> None:
        node = EnvironmentErrorNode(_MultipleFixesError(item="artifact"))

        assert node.content() == "Error: Problem with artifact.\n\nWays to fix:\n\n- Fix artifact.\n- Retry."

    def test_content__renders_multiline_message_as_block(self) -> None:
        node = EnvironmentErrorNode(_MultilineError())

        assert node.content() == "Error:\n\nFirst line.\nSecond line."

    def test_status__builds_error_cell(self) -> None:
        node = EnvironmentErrorNode(
            _SingleFixError(item="artifact", count=3, active=True, decimal_value=Decimal("1.5"))
        )

        cell = node.status()

        assert cell.kind == "sample_error"
        assert cell.media_type == "text/markdown"
        assert cell.content == "Sample: Problem with artifact.\nWay to fix: Fix artifact."
        assert cell.meta == {
            "error_code": "sample.single",
            "item": "artifact",
            "count": 3,
            "active": True,
            "decimal_value": "1.5",
        }

    def test_journal_message__renders_single_line_message(self) -> None:
        node = EnvironmentErrorNode(_MultilineError())

        assert node.journal_message() == "First line. Second line."


class TestEnvironmentErrorNodeShortcut:
    def test_returns_environment_error_node(self) -> None:
        error = _MultipleFixesError(item="artifact")

        node = environment_error_node(error)

        assert isinstance(node, EnvironmentErrorNode)
        assert node.status().meta["error_code"] == "sample.multiple"
