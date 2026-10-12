import datetime

import pytest
from llm_tool_cli.config.runtime import RuntimeConfig, runtime_config
from llm_tool_cli.config.tests.fixtures import runtime_settings
from llm_tool_cli.core.result import Ok, Result
from llm_tool_cli.protocol import Protocol
from llm_tool_cli.protocol import errors as protocol_errors
from pytest_mock import MockerFixture

from donna.context.journal import Journal
from donna.context.output import NoopEmitter, output
from donna.context.tests import make
from donna.context.tests.helpers import FakeOutputEmitter
from donna.machine import ExecutionContext
from donna.machine.caches import caches
from donna.machine.context import execution_context
from donna.machine.state import ConsistentState
from donna.machine.tests import make as machine_make


class _FakeStateCache:
    def __init__(self) -> None:
        self.state = machine_make.mutable_state(tasks=[machine_make.task()]).freeze()

    def load(self) -> Result[ConsistentState]:
        return Ok(self.state)

    def save(self, state: ConsistentState) -> Result[None]:
        self.state = state
        return Ok(None)


class TestJournal:
    @pytest.mark.parametrize(
        ("mode", "actor_id"),
        [
            (Protocol.human, "human"),
            (Protocol.llm, "agent"),
            (Protocol.automation, "automation"),
        ],
    )
    def test_smart_actor_id__depends_on_selected_protocol(
        self, mocker: MockerFixture, mode: Protocol, actor_id: str
    ) -> None:
        with runtime_config.scope(RuntimeConfig(protocol=mode)):
            assert Journal().smart_actor_id() == actor_id

    def test_smart_actor_id__raises_for_unsupported_mode(self, mocker: MockerFixture) -> None:
        with (
            runtime_config.scope(RuntimeConfig(protocol=Protocol.human).replace(protocol="unsupported")),
            pytest.raises(protocol_errors.UnsupportedFormatterMode),
        ):
            Journal().smart_actor_id()

    def test_add__builds_writes_and_emits_journal_record(self, mocker: MockerFixture) -> None:
        now = datetime.datetime(2026, 5, 18, 8, 30, tzinfo=datetime.UTC)
        active_caches = make.caches()
        active_caches.state = _FakeStateCache()
        emitter = FakeOutputEmitter()
        mocker.patch("donna.context.journal.now", return_value=now)
        write_record = mocker.patch("donna.context.journal.workspace_journal.write_record", return_value=Ok(None))

        with (
            runtime_config.scope(RuntimeConfig(protocol=Protocol.llm)),
            caches.scope(active_caches),
            output.scope(emitter),
            execution_context.scope(ExecutionContext(current_work_unit_id=machine_make.WORK_UNIT_ID)),
        ):
            with execution_context.scope(
                execution_context.get().replace(current_operation_id=machine_make.PRIMARY_OPERATION_ID)
            ):
                result = Journal().add("message")

        assert result.is_ok()
        record = result.unwrap()
        assert record.timestamp == now
        assert record.actor_id == "agent"
        assert record.message == "message"
        assert record.current_task_id == machine_make.TASK_ID
        assert record.current_work_unit_id == machine_make.WORK_UNIT_ID
        assert record.current_operation_id == machine_make.PRIMARY_OPERATION_ID
        write_record.assert_called_once_with(record)
        assert emitter.journal_records == [record]

    def test_add__uses_explicit_actor_id(self, mocker: MockerFixture) -> None:
        active_caches = make.caches()
        active_caches.state = _FakeStateCache()
        emitter = FakeOutputEmitter()
        mocker.patch("donna.context.journal.now", return_value=datetime.datetime(2026, 5, 18, tzinfo=datetime.UTC))
        mocker.patch("donna.context.journal.workspace_journal.write_record", return_value=Ok(None))
        smart_actor = mocker.patch.object(Journal, "smart_actor_id")

        with caches.scope(active_caches), execution_context.scope(ExecutionContext()), output.scope(emitter):
            result = Journal().add("message", actor_id="donna")

        assert result.is_ok()
        assert result.unwrap().actor_id == "donna"
        assert result.unwrap().current_work_unit_id is None
        assert result.unwrap().current_operation_id is None
        smart_actor.assert_not_called()

    def test_add__uses_current_output_scope_and_preserves_forwarding(self, mocker: MockerFixture) -> None:
        active_caches = make.caches()
        active_caches.state = _FakeStateCache()
        emitter = FakeOutputEmitter()
        journal = Journal()
        write_record = mocker.patch("donna.context.journal.workspace_journal.write_record", return_value=Ok(None))

        with caches.scope(active_caches), execution_context.scope(ExecutionContext()), output.scope(emitter):
            journal.add("before").unwrap()
            with pytest.raises(ValueError):
                with output.scope(NoopEmitter()):
                    journal.add("silent").unwrap()
                    raise ValueError("leave nested scope")
            journal.add("after").unwrap()

        assert [record.message for record in emitter.journal_records] == ["before", "after"]
        assert [call.args[0].message for call in write_record.call_args_list] == ["before", "silent", "after"]
        assert not output.is_set()


__all__ = ["runtime_settings"]

pytestmark = pytest.mark.usefixtures("runtime_settings")
