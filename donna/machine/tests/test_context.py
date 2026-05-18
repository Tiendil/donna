import pytest

from donna.machine import errors as machine_errors
from donna.machine.context import ValueScope, context, reset_context, set_context
from donna.machine.tests.helpers import FakeMachineContext


class TestValueScope:
    def test_get__returns_initial_value(self) -> None:
        scope = ValueScope("initial")

        assert scope.get() == "initial"

    def test_scope__restores_previous_value(self) -> None:
        scope = ValueScope("outer")

        with scope.scope("inner"):
            assert scope.get() == "inner"

        assert scope.get() == "outer"

    def test_scope__restores_previous_value_after_exception(self) -> None:
        scope = ValueScope("outer")

        with pytest.raises(ValueError):
            with scope.scope("inner"):
                raise ValueError

        assert scope.get() == "outer"


class TestContext:
    def test_context__raises_when_not_set(self) -> None:
        with pytest.raises(machine_errors.MachineContextNotSet):
            context()

    def test_context__returns_current_context_until_reset(self) -> None:
        machine_context = FakeMachineContext()
        token = set_context(machine_context)

        try:
            assert context() == machine_context
        finally:
            reset_context(token)

        with pytest.raises(machine_errors.MachineContextNotSet):
            context()
