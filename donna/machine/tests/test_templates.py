from typing import Any

import pytest

from donna.core.errors import ErrorsList
from donna.core.result import Err, Ok, Result
from donna.machine import errors as machine_errors
from donna.machine.templates import Directive, DirectiveUnsupportedRenderMode, RenderMode


class _Directive(Directive):
    analyze_id: str = "sample"

    def render_view(self, context: dict[str, Any], *argv: Any) -> Result[Any, ErrorsList]:
        return Ok({"mode": context["render_mode"], "argv": argv})


class _PreparingDirective(_Directive):
    def _prepare_arguments(
        self, context: dict[str, Any], *argv: Any, **kwargs: Any
    ) -> Result[tuple[Any, ...], ErrorsList]:
        return Ok(("prepared", *argv, kwargs["extra"]))


class _FailingDirective(_Directive):
    def _prepare_arguments(
        self, context: dict[str, Any], *argv: Any, **kwargs: Any
    ) -> Result[tuple[Any, ...], ErrorsList]:
        return Err([machine_errors.PrimitiveInvalidImportPath(import_path="bad")])


class TestDirective:
    def test_apply_directive__renders_view_mode(self) -> None:
        result = _Directive().apply_directive({"render_mode": RenderMode.view}, "value")

        assert result.is_ok()
        assert result.unwrap() == {"mode": RenderMode.view, "argv": ("value",)}

    def test_apply_directive__renders_execute_mode_with_view_default(self) -> None:
        result = _Directive().apply_directive({"render_mode": RenderMode.execute}, "value")

        assert result.is_ok()
        assert result.unwrap() == {"mode": RenderMode.execute, "argv": ("value",)}

    def test_apply_directive__renders_analysis_mode(self) -> None:
        result = _Directive().apply_directive({"render_mode": RenderMode.analysis}, "a", 2)

        assert result.is_ok()
        assert result.unwrap() == "$$donna sample a 2 donna$$"

    def test_apply_directive__uses_prepared_arguments(self) -> None:
        result = _PreparingDirective().apply_directive({"render_mode": RenderMode.view}, "value", extra="tail")

        assert result.is_ok()
        assert result.unwrap() == {"mode": RenderMode.view, "argv": ("prepared", "value", "tail")}

    def test_apply_directive__returns_argument_preparation_error(self) -> None:
        result = _FailingDirective().apply_directive({"render_mode": RenderMode.view})

        assert result.is_err()
        assert isinstance(result.unwrap_err()[0], machine_errors.PrimitiveInvalidImportPath)

    def test_apply_directive__rejects_unsupported_render_mode(self) -> None:
        with pytest.raises(DirectiveUnsupportedRenderMode) as exception_info:
            _Directive().apply_directive({"render_mode": "unsupported"})

        error = exception_info.value
        assert error.arguments == {"render_mode": "unsupported", "directive_name": "_Directive"}

    def test_render_analyze__omits_empty_argument_gap(self) -> None:
        result = _Directive().render_analyze({"render_mode": RenderMode.analysis})

        assert result.is_ok()
        assert result.unwrap() == "$$donna sample donna$$"
