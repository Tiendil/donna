import pytest

from donna.machine import errors as machine_errors
from donna.machine.context import context, reset_context, set_context
from donna.machine.tests.helpers import FakeMachineContext


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
