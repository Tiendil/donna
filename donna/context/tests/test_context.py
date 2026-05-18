import pytest

from donna.context.artifacts import ArtifactsCache
from donna.context.context import Context, context, reset_context, set_context
from donna.context.journal import Journal
from donna.context.output import NoopEmitter
from donna.context.primitives import PrimitivesCache
from donna.context.state import StateCache
from donna.context.tests.make import FakeOutputEmitter


class TestContext:
    def test_init__creates_invocation_local_caches_and_scopes(self) -> None:
        runtime_context = Context()

        assert isinstance(runtime_context.artifacts, ArtifactsCache)
        assert isinstance(runtime_context.state, StateCache)
        assert isinstance(runtime_context.primitives, PrimitivesCache)
        assert isinstance(runtime_context.journal, Journal)
        assert isinstance(runtime_context.output, NoopEmitter)
        assert runtime_context.current_work_unit_id.get() is None
        assert runtime_context.current_operation_id.get() is None

    def test_init__uses_explicit_output_emitter(self) -> None:
        output = FakeOutputEmitter()

        runtime_context = Context(output=output)

        assert runtime_context.output == output


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
