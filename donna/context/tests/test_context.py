import pytest

from donna.context.context import Context, context, reset_context, set_context
from donna.context.journal import Journal


class TestContext:
    def test_init__creates_invocation_local_services(self) -> None:
        runtime_context = Context()

        assert isinstance(runtime_context.journal, Journal)


class TestSetContext:
    def test_sets_current_context(self) -> None:
        runtime_context = Context()
        token = set_context(runtime_context)

        try:
            assert context() == runtime_context
        finally:
            reset_context(token)


class TestResetContext:
    def test_restores_previous_context(self) -> None:
        outer_context = Context()
        inner_context = Context()
        outer_token = set_context(outer_context)

        try:
            inner_token = set_context(inner_context)
            assert context() == inner_context

            reset_context(inner_token)

            assert context() == outer_context
        finally:
            reset_context(outer_token)


class TestContextFunction:
    def test_context__raises_when_not_set(self) -> None:
        with pytest.raises(RuntimeError):
            context()

    def test_context__returns_current_context(self) -> None:
        runtime_context = Context()
        token = set_context(runtime_context)

        try:
            assert context() == runtime_context
        finally:
            reset_context(token)

        with pytest.raises(RuntimeError):
            context()
